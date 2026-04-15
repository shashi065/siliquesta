"""Compute jobs endpoints with queue tracking and caching."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models import ComputeJob, User
from app.services.job_dispatcher import JobDispatcher
from app.services.job_queue import JobPriority, JobStatus, get_job_queue
from app.services.job_worker import get_job_worker

router = APIRouter()


# ============ Pydantic Models ============


class JobRequest(BaseModel):
    """Request to enqueue a new job."""

    job_type: str = Field(..., description="Job type: simulate, optimize, analyze")
    params: dict = Field(..., description="Job parameters")
    priority: Optional[str] = Field("normal", description="Priority: low, normal, high, urgent")


class JobResponse(BaseModel):
    """Response for queued job."""

    job_id: str = Field(..., description="Unique job ID")
    status: str = Field(..., description="Current status")
    created_at: str = Field(..., description="Creation timestamp")
    message: Optional[str] = None


class QueueStatsResponse(BaseModel):
    """Queue statistics."""

    total_jobs: int
    queued: int
    running: int
    completed: int
    failed: int
    estimated_wait_minutes: Optional[float] = None


class BatchJobRequest(BaseModel):
    """Request to enqueue multiple jobs."""

    jobs: list[JobRequest] = Field(..., description="List of jobs to enqueue")


@router.get("/mine")
async def list_my_jobs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ComputeJob)
        .where(ComputeJob.user_id == current_user.id)
        .order_by(ComputeJob.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    return {
        "jobs": [
            {
                "job_key": job.job_key,
                "scope": job.scope,
                "status": job.status,
                "priority": job.priority,
                "cost_credits": job.cost_credits,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "finished_at": job.finished_at.isoformat() if job.finished_at else None,
                "error_text": job.error_text,
            }
            for job in result.scalars().all()
        ]
    }


@router.get("/queue/status")
async def queue_status():
    return {
        "dispatcher": "celery",
        "celery_enabled": JobDispatcher.celery_enabled(),
        "broker": "redis",
    }


@router.get("/{job_key}")
async def get_job(
    job_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ComputeJob).where(
            (ComputeJob.job_key == job_key) | (ComputeJob.backend_task_id == job_key),
            ComputeJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    celery_status = None
    if job.backend_task_id:
        celery_status = JobDispatcher.status(job.backend_task_id)

    return {
        "job_id": job.backend_task_id or job.job_key,
        "job_key": job.job_key,
        "type": job.scope,
        "status": celery_status["status"] if celery_status else job.status,
        "result": celery_status.get("result") if celery_status else job.result_json,
        "error": job.error_text,
        "retry_count": job.retry_count,
        "created_at": job.created_at.isoformat(),
        "completed_at": job.finished_at.isoformat() if job.finished_at else None,
    }


# ============ NEW: Job Queue & Tracking Endpoints ============


@router.post("/enqueue", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_job(
    request: JobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Enqueue a simulation or optimization job asynchronously.
    
    Returns 202 Accepted immediately with job ID.
    Poll GET /jobs/{job_id} to check status.
    """
    try:
        priority = JobPriority(request.priority)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid priority. Must be: {', '.join([p.value for p in JobPriority])}",
        )

    job_queue = get_job_queue()
    job_key = job_queue.enqueue(
        job_type=request.job_type,
        params=request.params,
        user_id=current_user.id,
        priority=priority,
        db=db,
    )

    return JobResponse(
        job_id=job_key,
        status=JobStatus.QUEUED.value,
        created_at="now",
        message=f"Job queued. Poll GET /jobs/{job_key} for status",
    )


@router.post("/batch-enqueue", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def batch_enqueue(
    request: BatchJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Enqueue multiple jobs at once (parameter sweep, exploration).
    
    Useful for parallel design exploration and optimization.
    """
    if len(request.jobs) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 jobs per batch",
        )

    job_queue = get_job_queue()
    job_ids = []
    failed = 0

    for job_req in request.jobs:
        try:
            priority = JobPriority(job_req.priority)
        except ValueError:
            failed += 1
            continue

        job_key = job_queue.enqueue(
            job_type=job_req.job_type,
            params=job_req.params,
            user_id=current_user.id,
            priority=priority,
            db=db,
        )
        job_ids.append(job_key)

    return {
        "total_requested": len(request.jobs),
        "enqueued": len(job_ids),
        "failed": failed,
        "job_ids": job_ids,
        "message": f"Submitted {len(job_ids)} jobs to queue",
    }


@router.get("/queue/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    current_user: User = Depends(get_current_user),
) -> QueueStatsResponse:
    """Get current queue statistics.
    
    Shows how many jobs are queued, running, completed, failed.
    Estimates wait time based on queue depth and worker count.
    """
    job_queue = get_job_queue()
    stats = job_queue.get_queue_stats()

    # Estimate: 5s per job, 4 parallel workers
    queued = stats.get("queued", 0)
    estimated_wait = (queued / 4 * 5) / 60 if queued > 0 else 0

    return QueueStatsResponse(
        total_jobs=stats.get("total_jobs", 0),
        queued=queued,
        running=stats.get("running", 0),
        completed=stats.get("completed", 0),
        failed=stats.get("failed", 0),
        estimated_wait_minutes=round(estimated_wait, 2) if estimated_wait > 0 else None,
    )


@router.get("/worker/stats")
async def get_worker_stats(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get worker statistics (admin only).
    
    Shows worker health, cache hit rate, queue depth.
    """
    if current_user.plan != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    worker = get_job_worker()
    stats = worker.get_stats()
    
    return {
        "is_running": stats["is_running"],
        "num_workers": stats["num_workers"],
        "registered_handlers": stats["registered_handlers"],
        "queue": stats["queue_stats"],
        "cache": stats["cache_stats"],
    }


@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Cancel a queued job.
    
    Only works for queued jobs, not running ones.
    """
    job_queue = get_job_queue()
    job_data = job_queue.get_status(job_id)

    if not job_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}",
        )

    if job_data.get("user_id") != current_user.id and current_user.plan != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot cancel other user's job",
        )

    if job_data.get("status") != JobStatus.QUEUED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Can only cancel queued jobs. Current: {job_data.get('status')}",
        )

    # Mark as cancelled
    job_queue.mark_failed(job_id, "Cancelled by user", db)

    return {"job_id": job_id, "message": "Job cancelled"}

