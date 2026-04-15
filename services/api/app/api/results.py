"""Result lookup endpoints for async jobs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import ComputeJob, User
from app.services.job_dispatcher import JobDispatcher

router = APIRouter()


@router.get("/{job_id}")
async def get_result(
    job_id: str,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    query = select(ComputeJob).where(
        (ComputeJob.job_key == job_id) | (ComputeJob.backend_task_id == job_id)
    )
    if current_user is not None:
        query = query.where(ComputeJob.user_id == current_user.id)
    result = await db.execute(query)
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
