"""
FastAPI endpoints for ML-based CMOS prediction.

Exposes:
- POST /api/v1/predict - Make predictions with confidence scores
- GET /api/v1/predict/models - List available models
- POST /api/v1/predict/train - Train new model (admin only)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Optional
import logging
from pathlib import Path

from app.ml_prediction_model import XGBoostCMOSPredictor, train_and_save_model

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/predict", tags=["predictions"])

# Global predictor instance
_predictor: Optional[XGBoostCMOSPredictor] = None


def get_predictor() -> XGBoostCMOSPredictor:
    """Lazy load predictor."""
    global _predictor
    if _predictor is None:
        _predictor = XGBoostCMOSPredictor()
        try:
            _predictor.load("cmos_predictor_v1")
            logger.info("Loaded pre-trained model")
        except FileNotFoundError:
            logger.warning("No pre-trained model found. Train one using /train endpoint.")
    return _predictor


# ============================================================================
# Request/Response Models
# ============================================================================


class PredictionRequest(BaseModel):
    """Request body for prediction."""

    C: float = Field(..., gt=0, description="Capacitance (farads)")
    Id: float = Field(..., gt=0, description="Drain current (amperes)")
    VDD: float = Field(..., gt=0, description="Supply voltage (volts)")

    class Config:
        json_schema_extra = {
            "example": {
                "C": 5e-12,
                "Id": 2e-3,
                "VDD": 3.3
            }
        }


class PredictionOutput(BaseModel):
    """Single prediction output."""

    predicted_value: float = Field(..., description="Predicted value")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score (0-1)")
    upper_bound: float = Field(..., description="95% confidence interval upper bound")
    lower_bound: float = Field(..., description="95% confidence interval lower bound")
    model_r2: float = Field(..., description="Model R² score")
    feature_importance: Dict[str, float] = Field(..., description="Feature importance scores")
    timestamp: str = Field(..., description="Prediction timestamp")


class PredictionResponse(BaseModel):
    """Complete prediction response."""

    frequency: PredictionOutput = Field(..., description="Frequency prediction (GHz)")
    power: PredictionOutput = Field(..., description="Power prediction (mW)")
    delay: PredictionOutput = Field(..., description="Delay prediction (ns)")


class ModelInfo(BaseModel):
    """Information about trained model."""

    trained: bool
    training_date: Optional[str]
    training_samples: int
    feature_names: list
    performance_metrics: Dict


class TrainingRequest(BaseModel):
    """Request to train new model."""

    n_samples: int = Field(default=10000, ge=1000, le=100000)
    model_name: str = Field(default="cmos_predictor_v1")


class TrainingResponse(BaseModel):
    """Response from training."""

    status: str
    message: str
    model_name: str
    training_samples: int
    performance_metrics: Dict


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/", response_model=PredictionResponse, summary="Make CMOS prediction")
async def predict(request: PredictionRequest) -> PredictionResponse:
    """
    Predict CMOS parameters using trained XGBoost model.

    Returns predictions with confidence intervals for:
    - Frequency (GHz)
    - Power (mW)
    - Delay (ns)

    Example:
        ```json
        {
            "C": 5e-12,
            "Id": 2e-3,
            "VDD": 3.3
        }
        ```
    """
    try:
        predictor = get_predictor()

        if not predictor.metadata["trained"]:
            raise HTTPException(
                status_code=503,
                detail="Model not trained. Call /train endpoint first."
            )

        predictions = predictor.predict(request.C, request.Id, request.VDD)

        return PredictionResponse(
            frequency=PredictionOutput(**predictions["frequency"].to_dict()),
            power=PredictionOutput(**predictions["power"].to_dict()),
            delay=PredictionOutput(**predictions["delay"].to_dict()),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models", response_model=ModelInfo, summary="Get model information")
async def get_model_info():
    """
    Get information about the current model.

    Returns:
    - Training status
    - Model performance metrics
    - Feature names
    """
    try:
        predictor = get_predictor()
        return ModelInfo(**predictor.metadata)

    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/train", response_model=TrainingResponse, summary="Train new model")
async def train_model(request: TrainingRequest) -> TrainingResponse:
    """
    Train a new XGBoost model on synthetic CMOS simulation data.

    ⚠️ **Admin Only** - This may take several minutes.

    Args:
        n_samples: Number of training samples (1000-100000)
        model_name: Name to save model as

    Returns:
        Training status and performance metrics

    Example:
        ```json
        {
            "n_samples": 10000,
            "model_name": "cmos_predictor_v2"
        }
        ```
    """
    try:
        logger.info(f"Starting model training: {request.n_samples} samples")

        # Train new model
        predictor = train_and_save_model(
            n_samples=request.n_samples,
            model_name=request.model_name
        )

        # Update global instance
        global _predictor
        _predictor = predictor

        return TrainingResponse(
            status="success",
            message=f"Model trained and saved as {request.model_name}",
            model_name=request.model_name,
            training_samples=request.n_samples,
            performance_metrics=predictor.metadata["performance_metrics"],
        )

    except Exception as e:
        logger.error(f"Training error: {e}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")


@router.post("/batch", summary="Batch prediction")
async def batch_predict(requests: list[PredictionRequest]) -> list[PredictionResponse]:
    """
    Make predictions for multiple inputs at once.

    Useful for bulk prediction tasks.

    Returns:
        List of prediction responses
    """
    try:
        predictor = get_predictor()

        if not predictor.metadata["trained"]:
            raise HTTPException(
                status_code=503,
                detail="Model not trained."
            )

        results = []
        for req in requests:
            predictions = predictor.predict(req.C, req.Id, req.VDD)
            results.append(
                PredictionResponse(
                    frequency=PredictionOutput(**predictions["frequency"].to_dict()),
                    power=PredictionOutput(**predictions["power"].to_dict()),
                    delay=PredictionOutput(**predictions["delay"].to_dict()),
                )
            )

        return results

    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", summary="Health check")
async def health_check():
    """Check if prediction service is ready."""
    try:
        predictor = get_predictor()
        return {
            "status": "healthy",
            "model_trained": predictor.metadata["trained"],
            "training_date": predictor.metadata.get("training_date"),
            "training_samples": predictor.metadata.get("training_samples", 0),
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Export router
__all__ = ["router"]
