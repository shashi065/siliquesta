"""Testing-only endpoints for validation in non-production environments."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager

router = APIRouter()


class FailJobRequest(BaseModel):
    message: str = "Forced failure for testing."


class SleepJobRequest(BaseModel):
    seconds: float = 5.0


def _ensure_testing() -> None:
    if settings.APP_ENV.lower() not in {"test", "testing"}:
        raise HTTPException(status_code=404, detail="Not found.")


@router.post("/fail-job")
async def fail_job(
    req: FailJobRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    _ensure_testing()
    access = await SaaSManager.authorize(db, request, "testing.fail", current_user, cost_credits=0.0)
    job = await SaaSManager.create_job(db, "testing.fail", current_user, req.model_dump(), access.priority, 0.0)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for testing execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.debug_fail", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "testing.fail"}


@router.post("/sleep-job")
async def sleep_job(
    req: SleepJobRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    _ensure_testing()
    access = await SaaSManager.authorize(db, request, "testing.sleep", current_user, cost_credits=0.0)
    job = await SaaSManager.create_job(db, "testing.sleep", current_user, req.model_dump(), access.priority, 0.0)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for testing execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.debug_sleep", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "testing.sleep"}
