"""Async compute tasks executed by Celery workers."""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from celery.utils.log import get_task_logger
from sqlalchemy import select

from app.celery_app import celery_app
from app.database import async_session
from app.models import ComputeJob, User
from app.services.ai_router import HybridAIRouter
from app.services.cmos_engine import CMOSPhysicsEngine, ProcessCorner
from app.services.design_dna import DesignDNAService
from app.services.digital_twin_ml import DigitalTwinSurrogateService
from app.services.optimizer_engine import AutonomousDesignAgent
from app.services.output_validation import (
    validate_simulation_output,
    validate_optimization_output,
    format_simulation_for_api,
    format_optimization_for_api,
)
from app.services.pvt_spice_service import SpicePVTService
from app.services.rag_system import RAGSystem
from app.services.spice_engine import SpiceEngine
from app.services.validation_engine import ValidationEngine

logger = get_task_logger(__name__)

_rag = RAGSystem()
_ai_router = HybridAIRouter(_rag)
_twin = DigitalTwinSurrogateService()
_optimizer = AutonomousDesignAgent()
_validator = ValidationEngine(_twin)
_design_dna = DesignDNAService()


async def _load_job(job_key: str) -> ComputeJob | None:
    async with async_session() as db:
        result = await db.execute(select(ComputeJob).where(ComputeJob.job_key == job_key))
        return result.scalar_one_or_none()


async def _update_job(
    job_key: str,
    status: str,
    payload: dict[str, Any] | None = None,
    error_text: str | None = None,
    retry_count: int | None = None,
) -> None:
    async with async_session() as db:
        result = await db.execute(select(ComputeJob).where(ComputeJob.job_key == job_key))
        job = result.scalar_one_or_none()
        if job is None:
            return
        if status == "running":
            job.started_at = datetime.utcnow()
        if status in {"completed", "failed"}:
            job.finished_at = datetime.utcnow()
        job.status = status
        if payload is not None:
            job.result_json = payload
        if error_text is not None:
            job.error_text = error_text[:4000]
        if retry_count is not None:
            job.retry_count = retry_count
        await db.commit()
    logger.info("job.status", extra={"job_key": job_key, "status": status, "retry_count": retry_count})

def _retry_context(task) -> int:
    return getattr(task.request, "retries", 0)


async def _ingest_design_dna(
    user_id: int | None,
    scope: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any] | None,
    metadata: dict[str, Any] | None = None,
    title: str | None = None,
) -> None:
    if user_id is None:
        return
    async with async_session() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            return
        await _design_dna.ingest(
            db,
            user,
            source_scope=scope,
            title=title or scope,
            summary=None,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata,
        )
        await db.commit()


@celery_app.task(
    name="siliquesta.run_spice_simulation",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_spice_simulation(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        result = SpiceEngine.run_inverter_transient(**payload)
        
        # Validate simulation output
        try:
            validated = validate_simulation_output(result.__dict__)
            response = format_simulation_for_api(validated)
        except Exception as validation_err:
            # If validation fails, still return result but mark it invalid
            logger.warning(f"Simulation validation failed: {validation_err}")
            response = result.__dict__
            response["valid"] = False
            response["validation_error"] = str(validation_err)
        
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "simulation", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("spice simulation failed")
        raise


@celery_app.task(
    name="siliquesta.run_pvt_sweep",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_pvt_sweep(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        response = {
            "source": "spice",
            "spice_verified": True,
            "voltages": SpicePVTService.supported_voltages(payload["tech_node"]),
            "pvt_results": SpicePVTService.run_full_sweep(
                wn=payload["wn"],
                wp=payload["wp"],
                cl_ff=payload["cl_ff"],
                tech_node=payload["tech_node"],
            ),
        }
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "pvt.full", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("pvt sweep failed")
        raise


@celery_app.task(
    name="siliquesta.run_pvt_corner_summary",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_pvt_corner_summary(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        response = {
            "source": "spice",
            "spice_verified": True,
            "summary": SpicePVTService.corner_summary(
                wn=payload["wn"],
                wp=payload["wp"],
                vdd=payload["vdd"],
                temp=payload["temp"],
                cl_ff=payload["cl_ff"],
                tech_node=payload["tech_node"],
            ),
        }
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "pvt.summary", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("pvt corner summary failed")
        raise


@celery_app.task(
    name="siliquesta.run_ai_chat",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_ai_chat(self, job_key: str, message: str, context: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        result = asyncio.run(_ai_router.respond(message, context))
        payload = {
            "response": result.response,
            "source": result.source,
            "route": result.route,
            "confidence": result.confidence,
            "retrieved_titles": result.retrieved_titles,
        }
        asyncio.run(_update_job(job_key, "completed", payload=payload))
        asyncio.run(_ingest_design_dna(context.get("user_id"), "ai.chat", context, payload, {"route": result.route}))
        return payload
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("ai chat failed")
        raise


@celery_app.task(
    name="siliquesta.predict_digital_twin",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def predict_digital_twin(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        result = _twin.predict(
            wn=payload["wn"],
            wp=payload["wp"],
            vdd=payload["vdd"],
            temp=payload["temp"],
            cl_ff=payload["cl_ff"],
            tech_node=payload["tech_node"],
            corner=payload["corner"],
        )
        response = result.__dict__
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "twin.predict", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("twin predict failed")
        raise


@celery_app.task(
    name="siliquesta.validate_design",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def validate_design(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        async def _run():
            async with async_session() as db:
                user = None
                if payload.get("user_id"):
                    res = await db.execute(select(User).where(User.id == payload["user_id"]))
                    user = res.scalar_one_or_none()
                result = await _validator.validate_design(db, user, payload)
                await db.commit()
                return result
        response = asyncio.run(_run())
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "twin.validate", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("validation failed")
        raise


@celery_app.task(
    name="siliquesta.compute_aging",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def compute_aging(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        from app.services.cmos_engine import DigitalTwin
        response = DigitalTwin.compute_aging(**payload)
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "twin.aging", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("aging compute failed")
        raise


@celery_app.task(
    name="siliquesta.run_optimizer",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_optimizer(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        response = _optimizer.optimize(**payload)
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "optimizer.run", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("optimizer failed")
        raise


@celery_app.task(
    name="siliquesta.run_ml_optimizer",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_ml_optimizer(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    """ML-powered optimization using digital twin surrogate model."""
    from app.services.ai_ml_optimizer import MLOptimizer
    
    asyncio.run(_update_job(job_key, "running"))
    try:
        # Setup objective weights based on optimization goal
        objective_map = {
            "performance": {"freq": 0.5, "power": 0.2, "delay": 0.2, "efficiency": 0.1},
            "power": {"freq": 0.1, "power": 0.7, "delay": 0.1, "efficiency": 0.1},
            "efficiency": {"freq": 0.3, "power": 0.2, "delay": 0.1, "efficiency": 0.4},
            "balanced": {"freq": 0.3, "power": 0.3, "delay": 0.2, "efficiency": 0.2},
        }
        
        objective = payload.get("objective", "balanced")
        objectives = objective_map.get(objective, objective_map["balanced"])
        
        # Create optimizer
        optimizer = MLOptimizer(objectives=objectives)
        
        # Extract baseline parameters
        baseline_params = {
            "wn": payload.get("wn", 1.0),
            "wp": payload.get("wp", 2.0),
            "vdd": payload.get("vdd", 1.8),
            "temp": payload.get("temp", 27.0),
            "cl_ff": payload.get("cl_ff", 10.0),
            "tech_node": payload.get("tech_node", 7.0),
        }
        
        # Run optimization
        method = payload.get("method", "two_stage")
        iterations = payload.get("iterations", 100)
        
        result = optimizer.optimize(
            baseline_params=baseline_params,
            method=method,
            iterations=iterations,
            verbose=True,
        )
        
        # Generate report
        report = optimizer.get_optimization_report(result)
        
        # Validate and format response
        try:
            # Validate optimization output
            validated = validate_optimization_output({
                "optimized_params": result.optimized_params,
                "predicted_metrics": result.predicted_metrics,
                "confidence_score": result.confidence_score,
                "uncertainty": result.uncertainty,
                "improvements": result.improvement_vs_baseline,
                "algorithm": "ml",
                "iterations": payload.get("iterations", 100),
            })
            
            # Format for API
            response = format_optimization_for_api(validated)
            response["model_metadata"] = result.model_metadata
            response["recommendations"] = report.get("recommendations", [])
            response["optimization_path_sample"] = result.optimization_path[-20:] if result.optimization_path else []
            
        except Exception as validation_err:
            # If validation fails, still return result but mark it invalid
            logger.warning(f"Optimization validation failed: {validation_err}")
            response = {
                "optimized_params": result.optimized_params,
                "predicted_metrics": result.predicted_metrics,
                "confidence_score": result.confidence_score,
                "uncertainty": result.uncertainty,
                "improvements": result.improvement_vs_baseline,
                "valid": False,
                "validation_error": str(validation_err),
            }
        
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "optimizer.ml-optimize", payload, response))
        return response
        
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("ML optimizer failed")
        raise


@celery_app.task(
    name="siliquesta.run_batch_simulations",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_batch_simulations(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        sims = payload.get("simulations", [])
        results = []
        for sim in sims:
            corner = ProcessCorner[sim.get("corner", "TT")]
            result = CMOSPhysicsEngine.compute(
                wn=sim["wn"],
                wp=sim["wp"],
                vdd=sim["vdd"],
                temp=sim["temp"],
                cl_ff=sim["cl_ff"],
                corner=corner,
                tech_node=sim["tech_node"],
            )
            results.append(result.__dict__)
        response = {"results": results, "count": len(results)}
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "simulation.batch", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("batch simulation failed")
        raise


@celery_app.task(
    name="siliquesta.run_zero_sim_sweep",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def run_zero_sim_sweep(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        corner = ProcessCorner[payload["corner"]]
        response = CMOSPhysicsEngine.sweep_wn(
            wp=payload["wp"],
            vdd=payload["vdd"],
            temp=payload["temp"],
            cl_ff=payload["cl_ff"],
            corner=corner,
            tech_node=payload["tech_node"],
            max_wn=payload.get("max_wn", 5.0),
        )
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "simulation.zero-sim", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("zero sim sweep failed")
        raise


@celery_app.task(
    name="siliquesta.train_digital_twin",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def train_digital_twin(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        sample_count = int(payload.get("sample_count", 2000))
        prefer_spice = bool(payload.get("prefer_spice", False))
        rows = _twin.build_dataset(sample_count=sample_count, prefer_spice=prefer_spice)
        metadata = _twin.train(rows)
        response = {"status": "trained", "metadata": metadata}
        asyncio.run(_update_job(job_key, "completed", payload=response))
        asyncio.run(_ingest_design_dna(payload.get("user_id"), "twin.train", payload, response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("digital twin training failed")
        raise


@celery_app.task(
    name="siliquesta.debug_fail",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def debug_fail(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        raise RuntimeError(payload.get("message", "Forced failure for testing."))
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("debug failure task triggered")
        raise


@celery_app.task(
    name="siliquesta.debug_sleep",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 1},
    soft_time_limit=2,
    time_limit=3,
)
def debug_sleep(self, job_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    asyncio.run(_update_job(job_key, "running"))
    try:
        duration = float(payload.get("seconds", 5.0))
        import time
        time.sleep(duration)
        response = {"slept": duration}
        asyncio.run(_update_job(job_key, "completed", payload=response))
        return response
    except Exception as exc:
        asyncio.run(_update_job(job_key, "failed", error_text=str(exc), retry_count=_retry_context(self)))
        logger.exception("debug sleep task failed")
        raise
