"""Digital Twin API - ML-based reliability model."""

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.api.auth import get_current_user_optional
from app.database import get_db
from app.models import User
from app.services.job_dispatcher import JobDispatcher
from app.services.saas import SaaSManager
from pathlib import Path
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter()


class DigitalTwinRequest(BaseModel):
    wn: float
    wp: float
    vdd: float
    temp: float
    cl_ff: float = 10.0
    tech_node: float = 28
    corner: str = "TT"
    years: int = 10


class DigitalTwinPredictResponse(BaseModel):
    delay_ps: float
    power_mw: float
    freq_ghz: float
    confidence: float
    estimated_error_percent: float
    model_source: str
    training_samples: int
    trained_with_spice: bool
    feature_importance: dict[str, float]


class DigitalTwinMLResponse(BaseModel):
    """Direct ML model prediction response."""
    power_mw: float
    power_confidence: float
    power_error_margin: float
    frequency_ghz: float
    frequency_confidence: float
    frequency_error_margin: float
    delay_ps: float
    delay_confidence: float
    delay_error_margin: float
    model_version: str
    trained_samples: int
    model_source: str = "xgboost"


class FeatureContribution(BaseModel):
    """Feature contribution to prediction."""
    wn: float
    wp: float
    vdd: float
    temp: float


class ExplanationResponse(BaseModel):
    """SHAP explanation response."""
    output: str  # "power", "frequency", or "delay"
    base_value: float
    contributions: FeatureContribution
    total_contribution: float
    prediction_value: float
    explanation_method: str = "shap"


class LifetimeBreakdown(BaseModel):
    """Lifetime for each degradation mechanism."""
    nbti: float  # Years
    hci: float   # Years
    em: float    # Years
    overall: float  # Years (minimum)


class ReliabilityResponse(BaseModel):
    """Device reliability and lifetime estimate."""
    reliability_score: float  # [0, 1] where 1=fresh, 0=failed
    time_in_operation: float  # Years
    nbti_shift_mv: float  # Threshold voltage shift (mV)
    hci_degradation: float  # Current degradation [0, 1]
    em_resistance_factor: float  # Relative resistance increase [1, inf)
    frequency_loss: float  # Frequency degradation [0, 1]
    nbti_factor: float  # Normalized NBTI degradation [0, 1]
    hci_factor: float  # Normalized HCI degradation [0, 1]
    em_factor: float  # Normalized EM degradation [0, 1]
    lifetime_years: LifetimeBreakdown  # Lifetime estimates
    dominant_failure_mode: str  # "NBTI", "HCI", or "Electromigration"


class DigitalTwinTrainRequest(BaseModel):
    sample_count: int = 2000
    prefer_spice: bool = False


class OrchestratorDesign(BaseModel):
    """Single design point from orchestrator."""
    design_id: str  # e.g., "design_0", "design_1"
    wn: float
    wp: float
    vdd: float
    temp: float
    cl_ff: float = 10.0
    # Predictions
    power_mw: float
    frequency_ghz: float
    delay_ps: float
    # Reliability
    reliability_score: float
    lifetime_years: float
    dominant_failure_mode: str
    # Model confidence
    prediction_confidence: float


class OrchestratorResponse(BaseModel):
    """Orchestrator response with best design, Pareto front, and explanations."""
    intent: str  # Parsed user intent
    constraints: Dict[str, Any]  # Extracted constraints
    best_design: OrchestratorDesign
    pareto_front: List[OrchestratorDesign]  # Non-dominated designs
    best_design_explanation: Dict[str, Any]  # SHAP explanations
    design_count: int  # Number of designs evaluated
    dominant_metric: str  # "power", "frequency", "reliability", or "balanced"
    trade_offs: Dict[str, Any]  # Trade-off analysis
    recommendations: List[str]  # Engineering recommendations


class OrchestratorRequest(BaseModel):
    """High-level user request for the orchestrator."""
    intent: str  # User query: "minimize power", "maximize frequency", "balance all", etc.
    constraints: Optional[Dict[str, Any]] = None  # Override constraints: {"max_power": 5.0, "min_freq": 1.0}
    reference_design: Optional[Dict[str, Any]] = None  # Reference point: {"wn": 2.0, "wp": 3.0, ...}
    num_designs: int = 20  # Number of designs to explore
    vdd: float = 1.8
    temp: float = 27.0
    cl_ff: float = 10.0


def _load_ml_trainer():
    """Load the trained Digital Twin ML models lazily.
    
    Returns DigitalTwinTrainer instance with loaded models, or None if not available.
    """
    try:
        import sys
        from pathlib import Path
        
        # Add the root directory to path to import train_digital_twin
        root_dir = Path(__file__).parent.parent.parent.parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        
        from train_digital_twin import DigitalTwinTrainer
        
        trainer = DigitalTwinTrainer()
        trainer.load_models()
        return trainer
    except Exception as e:
        logger.warning(f"Failed to load Digital Twin ML models: {e}")
        return None


@router.post("/predict/ml", response_model=DigitalTwinMLResponse)
async def predict_operating_point_ml(
    req: DigitalTwinRequest,
):
    """
    Direct ML-based prediction using trained XGBoost models.
    Fast, zero-latency predictions for power, frequency, and delay.
    
    Returns confidence scores and error margins for each prediction.
    No authentication required for fast predictions.
    """
    trainer = _load_ml_trainer()
    if trainer is None:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Train models using /predict endpoint."
        )
    
    try:
        # Get predictions from the trained models
        predictions = trainer.predict(
            wn=req.wn,
            wp=req.wp,
            vdd=req.vdd,
            temp=req.temp
        )
        
        # Extract model version from metadata if available
        model_version = "v1"
        trained_samples = 5000
        if hasattr(trainer, 'metadata'):
            model_version = trainer.metadata.get("version", "v1")
            trained_samples = trainer.metadata.get("training_samples", 5000)
        
        return DigitalTwinMLResponse(
            power_mw=predictions["power"]["value"],
            power_confidence=predictions["power"]["confidence"],
            power_error_margin=predictions["power"]["error_margin"],
            frequency_ghz=predictions["frequency"]["value"],
            frequency_confidence=predictions["frequency"]["confidence"],
            frequency_error_margin=predictions["frequency"]["error_margin"],
            delay_ps=predictions["delay"]["value"] * 1000,  # Convert ns to ps
            delay_confidence=predictions["delay"]["confidence"],
            delay_error_margin=predictions["delay"]["error_margin"] * 1000,  # Convert ns to ps
            model_version=model_version,
            trained_samples=trained_samples,
            model_source="xgboost"
        )
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/xai", response_model=ExplanationResponse)
async def explain_prediction(
    wn: float,
    wp: float,
    vdd: float,
    temp: float,
    output: str = "power"
):
    """
    Get SHAP explanations for a Digital Twin prediction.
    
    Returns feature contributions for each input variable.
    Explains how much each feature (wn, wp, vdd, temp) influences the model's prediction.
    
    Args:
        wn: NMOS width (µm)
        wp: PMOS width (µm)
        vdd: Supply voltage (V)
        temp: Temperature (°C)
        output: Which output to explain ("power", "frequency", "delay") - default: "power"
    """
    if output not in ["power", "frequency", "delay"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid output '{output}'. Must be 'power', 'frequency', or 'delay'."
        )
    
    trainer = _load_ml_trainer()
    if trainer is None:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Train models using /predict endpoint."
        )
    
    if not hasattr(trainer, 'explainers') or not trainer.explainers:
        raise HTTPException(
            status_code=503,
            detail="SHAP explainers not available. Models may need to be retrained."
        )
    
    try:
        # Get SHAP explanation
        explanation = trainer.explain_prediction(
            wn=wn,
            wp=wp,
            vdd=vdd,
            temp=temp,
            output_name=output
        )
        
        if "error" in explanation:
            raise HTTPException(
                status_code=500,
                detail=explanation["error"]
            )
        
        # Convert to response model
        return ExplanationResponse(
            output=output,
            base_value=explanation["base_value"],
            contributions=FeatureContribution(
                wn=explanation["contributions"]["wn"],
                wp=explanation["contributions"]["wp"],
                vdd=explanation["contributions"]["vdd"],
                temp=explanation["contributions"]["temp"]
            ),
            total_contribution=explanation["total_contribution"],
            prediction_value=explanation["prediction_value"],
            explanation_method="shap"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SHAP explanation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Explanation failed: {str(e)}"
        )


@router.get("/reliability", response_model=ReliabilityResponse)
async def compute_device_reliability(
    vdd: float = Query(..., ge=0.5, le=3.3, description="Supply voltage (V)"),
    temp: float = Query(..., ge=-40, le=150, description="Temperature (°C)"),
    time_years: float = Query(10.0, ge=0.1, le=100, description="Operating time in years"),
    current_ma: float = Query(1.0, ge=0.1, le=100, description="Operating current (mA)"),
) -> ReliabilityResponse:
    """
    Compute device reliability metrics and lifetime estimates.
    
    Calculates degradation due to:
    - NBTI (Negative Bias Temperature Instability)
    - HCI (Hot Carrier Injection)
    - Electromigration
    
    Returns reliability score [0,1] where 1=fresh device, 0=end-of-life.
    """
    try:
        from train_digital_twin import ReliabilityModel
        
        model = ReliabilityModel()
        result = model.compute_reliability_score(vdd, temp, time_years, current_ma)
        
        return ReliabilityResponse(
            reliability_score=result["reliability_score"],
            time_in_operation=result["time_in_operation"],
            nbti_shift_mv=result["nbti_shift_mv"],
            hci_degradation=result["hci_degradation"],
            em_resistance_factor=result["em_resistance_factor"],
            frequency_loss=result["frequency_loss"],
            nbti_factor=result["nbti_factor"],
            hci_factor=result["hci_factor"],
            em_factor=result["em_factor"],
            lifetime_years=LifetimeBreakdown(**result["lifetime_years"]),
            dominant_failure_mode=result["dominant_failure_mode"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reliability computation error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Reliability computation failed: {str(e)}"
        )


@router.post("/orchestrate", response_model=OrchestratorResponse)
async def orchestrate_design_search(
    req: OrchestratorRequest,
) -> OrchestratorResponse:
    """
    AI Orchestrator: Unified design space exploration.
    
    Combines optimizer, predictor, and reliability model to find optimal designs.
    
    Flow:
    1. Parse user intent (minimize power, maximize frequency, balance)
    2. Extract constraints (max power, min frequency, lifetime)
    3. Generate candidate designs via sampling
    4. Call predictor for performance metrics
    5. Call reliability for lifetime assessment
    6. Identify Pareto front
    7. Generate SHAP explanations
    8. Return results with recommendations
    """
    try:
        trainer = _load_ml_trainer()
        if trainer is None:
            raise HTTPException(
                status_code=503,
                detail="ML models not available. Train models first."
            )
        
        from train_digital_twin import ReliabilityModel
        import numpy as np
        
        # === STEP 1: Parse User Intent ===
        intent_lower = req.intent.lower()
        if "power" in intent_lower and "min" in intent_lower:
            primary_objective = "power"
            dominant_metric = "power"
        elif "freq" in intent_lower and "max" in intent_lower:
            primary_objective = "frequency"
            dominant_metric = "frequency"
        elif "reliab" in intent_lower:
            primary_objective = "reliability"
            dominant_metric = "reliability"
        else:
            primary_objective = "balanced"
            dominant_metric = "balanced"
        
        logger.info(f"Parsed intent: {primary_objective}")
        
        # === STEP 2: Extract Constraints ===
        constraints = {
            "max_power_mw": 10.0,  # Default
            "min_frequency_ghz": 0.5,  # Default
            "min_lifetime_years": 5.0,  # Default
            "max_temp_c": 100.0,
            "vdd_v": req.vdd,
            "temp_c": req.temp,
        }
        if req.constraints:
            constraints.update(req.constraints)
        
        logger.info(f"Constraints: {constraints}")
        
        # === STEP 3: Generate Candidate Designs ===
        np.random.seed(42)  # Reproducibility
        candidates = []
        
        # Use Latin Hypercube Sampling for better coverage
        wn_range = np.linspace(0.5, 5.0, req.num_designs // 2)
        wp_range = np.linspace(1.0, 10.0, req.num_designs // 2)
        
        for wn in wn_range:
            for wp in wp_range:
                if len(candidates) < req.num_designs:
                    candidates.append({
                        "wn": float(wn),
                        "wp": float(wp),
                        "vdd": req.vdd,
                        "temp": req.temp,
                        "cl_ff": req.cl_ff,
                    })
        
        logger.info(f"Generated {len(candidates)} candidate designs")
        
        # === STEP 4: Predict Performance & Reliability for Each Design ===
        evaluated_designs = []
        
        for idx, cand in enumerate(candidates[:req.num_designs]):
            try:
                # Predict using ML surrogate
                pred = trainer.predict(
                    wn=cand["wn"],
                    wp=cand["wp"],
                    vdd=cand["vdd"],
                    temp=cand["temp"]
                )
                
                # Compute reliability
                reliability_model = ReliabilityModel()
                reliability_result = reliability_model.compute_reliability_score(
                    vdd=cand["vdd"],
                    temp=cand["temp"],
                    time_years=10.0,
                    current_ma=1.0
                )
                
                lifetime_data = reliability_model.compute_lifetime(
                    vdd=cand["vdd"],
                    temp=cand["temp"],
                    current_ma=1.0
                )
                
                design = OrchestratorDesign(
                    design_id=f"design_{idx}",
                    wn=cand["wn"],
                    wp=cand["wp"],
                    vdd=cand["vdd"],
                    temp=cand["temp"],
                    cl_ff=cand.get("cl_ff", 10.0),
                    power_mw=pred["power"]["value"],
                    frequency_ghz=pred["frequency"]["value"],
                    delay_ps=pred.get("delay", {}).get("value", 1.0 / pred["frequency"]["value"]),
                    reliability_score=reliability_result["reliability_score"],
                    lifetime_years=lifetime_data["overall"],
                    dominant_failure_mode=reliability_result["dominant_failure_mode"],
                    prediction_confidence=min(
                        pred["power"]["confidence"],
                        pred["frequency"]["confidence"]
                    ),
                )
                
                # Check constraints
                if (design.power_mw <= constraints.get("max_power_mw", 100.0) and
                    design.frequency_ghz >= constraints.get("min_frequency_ghz", 0.0) and
                    design.lifetime_years >= constraints.get("min_lifetime_years", 0.0)):
                    evaluated_designs.append(design)
                
            except Exception as e:
                logger.warning(f"Failed to evaluate design {idx}: {e}")
                continue
        
        if not evaluated_designs:
            raise HTTPException(
                status_code=400,
                detail="No designs satisfied the constraints. Relax constraints and retry."
            )
        
        logger.info(f"Evaluated {len(evaluated_designs)} designs that meet constraints")
        
        # === STEP 5: Identify Pareto Front ===
        def is_dominated(design, others):
            """Check if design is dominated by any other."""
            for other in others:
                if other is design:
                    continue
                # Dominated if all objectives are worse or equal
                power_worse = design.power_mw > other.power_mw * 1.01
                freq_worse = design.frequency_ghz < other.frequency_ghz * 0.99
                reliability_worse = design.reliability_score < other.reliability_score * 0.99
                
                if (power_worse and freq_worse) or (power_worse and reliability_worse) or (freq_worse and reliability_worse):
                    return True
            return False
        
        pareto_front = [d for d in evaluated_designs if not is_dominated(d, evaluated_designs)]
        
        # Sort by primary objective
        if primary_objective == "power":
            pareto_front.sort(key=lambda d: d.power_mw)
        elif primary_objective == "frequency":
            pareto_front.sort(key=lambda d: -d.frequency_ghz)
        elif primary_objective == "reliability":
            pareto_front.sort(key=lambda d: -d.reliability_score)
        
        logger.info(f"Identified {len(pareto_front)} Pareto-optimal designs")
        
        # === STEP 6: Select Best Design ===
        best_design = pareto_front[0]
        
        # === STEP 7: Generate Explanation for Best Design ===
        explanation_dict = {}
        try:
            explanation = trainer.explain_prediction(
                wn=best_design.wn,
                wp=best_design.wp,
                vdd=best_design.vdd,
                temp=best_design.temp,
                output_name="power"
            )
            explanation_dict = {
                "output": "power",
                "base_value": explanation.get("base_value", 0),
                "contributions": explanation.get("contributions", {}),
                "method": "shap"
            }
        except Exception as e:
            logger.warning(f"Failed to generate explanation: {e}")
        
        # === STEP 8: Compute Trade-off Analysis ===
        trade_offs = {
            "power_range_mw": [min(d.power_mw for d in pareto_front), max(d.power_mw for d in pareto_front)],
            "frequency_range_ghz": [min(d.frequency_ghz for d in pareto_front), max(d.frequency_ghz for d in pareto_front)],
            "reliability_range": [min(d.reliability_score for d in pareto_front), max(d.reliability_score for d in pareto_front)],
            "designs_on_frontier": len(pareto_front),
        }
        
        # === STEP 9: Generate Recommendations ===
        recommendations = []
        if best_design.power_mw < 2.0:
            recommendations.append("✓ Low-power design: Good for battery-constrained applications")
        if best_design.frequency_ghz > 2.0:
            recommendations.append("✓ High-performance design: Suitable for compute-intensive tasks")
        if best_design.reliability_score > 0.9:
            recommendations.append("✓ Highly reliable: Extended device lifetime expected")
        if len(pareto_front) > 5:
            recommendations.append(f"✓ {len(pareto_front)} alternative designs available for trade-off exploration")
        
        if not recommendations:
            recommendations.append("Design meets specified constraints")
        
        return OrchestratorResponse(
            intent=req.intent,
            constraints=constraints,
            best_design=best_design,
            pareto_front=pareto_front[:10],  # Top 10 from Pareto front
            best_design_explanation=explanation_dict,
            design_count=len(evaluated_designs),
            dominant_metric=dominant_metric,
            trade_offs=trade_offs,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Orchestrator error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Orchestration failed: {str(e)}"
        )


@router.post("/predict")
async def predict_operating_point(
    req: DigitalTwinRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Predict delay, power, and frequency using the trained Digital Twin surrogate.
    The model auto-bootstraps a training artifact if none exists yet.
    """
    access = await SaaSManager.authorize(db, request, "twin.predict", current_user)
    job = await SaaSManager.create_job(db, "twin.predict", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for digital twin execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.predict_digital_twin", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "twin.predict"}


@router.post("/compute-aging")
async def queue_compute_aging(
    req: DigitalTwinRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute device aging effects:
    - NBTI (PMOS threshold shift)
    - HCI (NMOS current degradation)
    - Electromigration (lifetime)
    """
    access = await SaaSManager.authorize(db, request, "twin.compute-aging", current_user)
    job = await SaaSManager.create_job(db, "twin.compute-aging", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for aging execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.compute_aging", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "twin.compute-aging"}


@router.post("/validate")
async def validate_digital_twin(
    req: DigitalTwinRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "twin.predict", current_user)
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


@router.post("/train")
async def train_digital_twin(
    req: DigitalTwinTrainRequest,
    request: Request,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    access = await SaaSManager.authorize(db, request, "twin.train", current_user)
    job = await SaaSManager.create_job(db, "twin.train", current_user, req.model_dump(), access.priority, access.cost_credits)
    await db.commit()
    if not JobDispatcher.celery_enabled():
        raise HTTPException(status_code=503, detail="Celery is required for training execution.")
    payload = req.model_dump()
    payload["user_id"] = current_user.id if current_user is not None else None
    task_id = JobDispatcher.dispatch("siliquesta.train_digital_twin", job.job_key, payload)
    await SaaSManager.attach_task_id(job, task_id)
    await db.commit()
    return {"job_id": task_id, "job_key": job.job_key, "status": "queued", "scope": "twin.train"}


def _get_health_recommendations(health_score: float) -> dict:
    """Get AVS/mitigation recommendations based on health"""
    if health_score > 90:
        return {
            "status": "HEALTHY",
            "action": "Normal operation",
            "vdd_boost": 0,
        }
    elif health_score > 75:
        return {
            "status": "AGING",
            "action": f"Apply AVS boost",
            "vdd_boost": 30,  # mV
        }
    else:
        return {
            "status": "CRITICAL",
            "action": "Throttle frequency or increase VDD significantly",
            "vdd_boost": 100,  # mV
        }
