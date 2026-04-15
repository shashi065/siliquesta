"""Simulation API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.api.auth import get_current_user_optional
from app.models import User
from app.services.design_dna import DesignDNAService
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager

router = APIRouter()
design_dna_service = DesignDNAService()


class SimulationRequest(BaseModel):
    """CMOS simulation request"""
    wn: float  # NMOS width (µm)
    wp: float  # PMOS width (µm)
    vdd: float  # Supply voltage (V)
    temp: float  # Temperature (°C)
    cl_ff: float  # Load capacitance (fF)
    corner: str = "TT"  # Process corner
    tech_node: float = 28  # Technology node (nm)


class SimulationResponse(BaseModel):
    """CMOS simulation response"""
    freq: float  # GHz
    power: float  # mW
    delay: float  # ps
    fom: float
    id_n: float  # µA
    id_p: float  # µA
    vth: float
    cox: float
    vov: float
    source: str = "spice"
    spice_verified: bool = True


@router.post("/")
async def submit_simulation_run(
    req: SimulationRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "simulate.run", current_user)
    job = await SaaSManager.create_job(db, "simulate.run", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for simulation execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_spice_simulation", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "simulate.run"}


@router.post("/sweep")
async def submit_sweep_simulation(
    req: SimulationRequest,
    request: Request,
    max_wn: float = 5.0,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "simulate.batch", current_user, cost_credits=6.0)
    job = await SaaSManager.create_job(db, "simulate.batch", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for sweep execution.")
    payload = req.model_dump() | {"max_wn": max_wn}
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_zero_sim_sweep", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "simulate.batch"}


class BatchRequest(BaseModel):
    """Multiple simulations"""
    simulations: list[SimulationRequest]


@router.post("/batch")
async def submit_batch_simulation(
    req: BatchRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "simulate.batch", current_user, cost_credits=max(8.0, len(req.simulations) * 1.5))
    job = await SaaSManager.create_job(
        db,
        "simulate.batch",
        current_user,
        {"count": len(req.simulations)},
        access.priority,
        access.cost_credits,
    )
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for batch execution.")
    payload = {"simulations": [item.model_dump() for item in req.simulations]}
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_batch_simulations", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "simulate.batch"}
