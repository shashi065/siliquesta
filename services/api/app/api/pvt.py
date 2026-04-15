"""PVT Analysis API."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.design_dna import DesignDNAService
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager

router = APIRouter()
design_dna_service = DesignDNAService()


class PVTRequest(BaseModel):
    wn: float
    wp: float
    cl_ff: float
    tech_node: float = 28
    prefer_spice: bool = True


@router.post("/corner-summary")
async def get_corner_summary(
    req: PVTRequest,
    request: Request,
    vdd: float = 1.2,
    temp: float = 27,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "pvt.corner-summary", current_user)
    job = await SaaSManager.create_job(
        db,
        "pvt.corner-summary",
        current_user,
        {**req.model_dump(), "vdd": vdd, "temp": temp},
        access.priority,
        access.cost_credits,
    )
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for PVT execution.")
    payload = {**req.model_dump(), "vdd": vdd, "temp": temp}
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_pvt_corner_summary", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "pvt.corner-summary"}


@router.post("/full-sweep")
async def full_pvt_sweep(
    req: PVTRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Run complete PVT analysis (all corners × temps × voltages)."""
    access = await SaaSManager.authorize(db, request, "pvt.full-sweep", current_user)
    job = await SaaSManager.create_job(db, "pvt.full-sweep", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for PVT execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_pvt_sweep", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "pvt.full-sweep"}
