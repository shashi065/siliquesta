"""Hybrid AI Service API for SILIQUESTA."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    message: str = Field(validation_alias=AliasChoices("message", "prompt"))
    context: dict = {}


class ChatResponse(BaseModel):
    response: str
    source: str
    confidence: float = 1.0
    route: str = "unknown"
    retrieval_count: int = 0
    retrieved_titles: list[str] = []


@router.post("/chat")
async def ai_chat(
    req: ChatRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Chat with the local hybrid SILIQUESTA AI stack."""
    access = await SaaSManager.authorize(db, request, "ai.chat", current_user)
    job = await SaaSManager.create_job(db, "ai.chat", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for AI execution.")
    context = dict(req.context)
    context["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_ai_chat", job.job_key, req.message, context)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "ai.chat"}


class GenerateCodeRequest(BaseModel):
    prompt: str
    language: str = "verilog"
    context: dict = {}


@router.post("/generate-code")
async def generate_code(
    req: GenerateCodeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate design code using the local LLM when available, with hybrid fallback."""
    access = await SaaSManager.authorize(db, request, "ai.generate-code", current_user)
    job = await SaaSManager.create_job(db, "ai.generate-code", current_user, req.model_dump(), access.priority, access.cost_credits)
    await SaaSManager.start_job(job)
    await db.commit()
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for AI execution.")
    context = dict(req.context)
    context["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.run_ai_chat", job.job_key, f"Generate {req.language} code for: {req.prompt}", context)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "ai.generate-code"}


class FailurePredictRequest(BaseModel):
    design_params: dict
    hours: int = 24


@router.post("/predict-failure")
async def predict_failure(
    req: FailurePredictRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Local predictive guidance for short-horizon design risk."""
    access = await SaaSManager.authorize(db, request, "ai.predict-failure", current_user)
    job = await SaaSManager.create_job(db, "ai.predict-failure", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for AI execution.")
    context = {
        "design_params": req.design_params,
        "prediction_horizon_hours": req.hours,
        "user_id": current_user.id if current_user is not None else None,
    }
    task_id = JobDispatcher.dispatch(
        "siliquesta.run_ai_chat",
        job.job_key,
        "Predict likely timing, power, or reliability failure risk for this design over the next operating window.",
        context,
    )
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "ai.predict-failure"}
