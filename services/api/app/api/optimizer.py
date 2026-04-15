"""ADA Optimizer API - Autonomous Design Agent."""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager

logger = logging.getLogger(__name__)

router = APIRouter()


class OptimizationRequest(BaseModel):
    wn: float = 0.5
    wp: float
    vdd: float
    temp: float
    cl_ff: float
    corner: str = "TT"
    tech_node: float = 28
    max_power: float = 5.0  # mW
    min_freq: float = 1.0  # GHz
    min_lifetime_years: float = 10.0
    population_size: int = 48
    generations: int = 10


@router.post("/")
async def run_optimization(
    req: OptimizationRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    ADA Optimizer - reference-guided multi-objective evolutionary search.
    """
    access = await SaaSManager.authorize(db, request, "optimizer.run", current_user)
    job = await SaaSManager.create_job(db, "optimizer.run", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for optimization execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_optimizer", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "optimizer.run"}


class MLOptimizeRequest(BaseModel):
    """ML-powered optimization request using digital twin surrogate model."""
    wn: float = 1.0
    wp: float = 2.0
    vdd: float = 1.8
    temp: float = 27.0
    cl_ff: float = 10.0
    tech_node: float = 7.0
    corner: str = "TT"
    objective: str = "performance"  # "performance", "efficiency", "power", "balanced"
    iterations: int = 100
    method: str = "two_stage"  # "two_stage", "evolutionary", "bayesian"


@router.post("/ml-optimize")
async def run_ml_optimization(
    req: MLOptimizeRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    ML-powered optimization using digital twin surrogate model.
    
    Provides fast parameter optimization with confidence scores and predictions.
    Much faster than brute-force simulation-based optimization.
    """
    access = await SaaSManager.authorize(db, request, "optimizer.ml-optimize", current_user)
    job = await SaaSManager.create_job(db, "optimizer.ml-optimize", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for optimization execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_ml_optimizer", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "optimizer.ml-optimize"}


class PredictPerformanceRequest(BaseModel):
    """Request to predict circuit performance using ML model."""
    wn: float
    wp: float
    vdd: float
    temp: float = 27.0
    cl_ff: float = 10.0
    tech_node: float = 7.0
    corner: str = "TT"


@router.post("/predict")
async def predict_performance(
    req: PredictPerformanceRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict circuit performance using digital twin ML model.
    
    Returns predicted metrics with confidence scores and uncertainty bounds.
    """
    from app.services.digital_twin_ml import DigitalTwinSurrogateService
    
    try:
        service = DigitalTwinSurrogateService()
        prediction = service.predict_with_confidence(
            wn=req.wn,
            wp=req.wp,
            vdd=req.vdd,
            temp=req.temp,
            cl_ff=req.cl_ff,
            tech_node=req.tech_node,
            corner=req.corner,
        )
        
        return {
            "optimized_params": {
                "wn": req.wn,
                "wp": req.wp,
                "vdd": req.vdd,
                "temp": req.temp,
                "cl_ff": req.cl_ff,
                "tech_node": req.tech_node,
                "corner": req.corner,
            },
            "predictedMetrics": {
                "delay_ps": prediction.delay_ps,
                "power_mw": prediction.power_mw,
                "freq_ghz": prediction.freq_ghz,
            },
            "confidenceScore": prediction.confidence,
            "uncertainty": prediction.uncertainty,
            "estimated_error_percent": prediction.estimated_error_percent,
            "model_metadata": {
                "model_source": prediction.model_source,
                "training_samples": prediction.training_samples,
                "trained_with_spice": prediction.trained_with_spice,
                "dataset_version": prediction.dataset_version,
                "validation_metrics": prediction.validation_metrics,
            },
        }
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
