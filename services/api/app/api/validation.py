"""Validation API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager
router = APIRouter()


class ValidateDesignRequest(BaseModel):
    wn: float
    wp: float
    vdd: float
    temp: float
    cl_ff: float
    tech_node: float = 28
    corner: str = "TT"


@router.post("/")
async def validate_design(
    req: ValidateDesignRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "twin.predict", current_user, cost_credits=8.0)
    job = await SaaSManager.create_job(db, "twin.validate", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for validation execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.validate_design", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "twin.validate"}
