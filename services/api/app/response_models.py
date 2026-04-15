"""Response standardization and validation for SILIQUESTA API."""

from typing import Any, Dict, Optional, List, TypeVar
from datetime import datetime
from pydantic import BaseModel, Field


T = TypeVar("T")


class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = True
    data: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    request_id: Optional[str] = None


class JobResponse(BaseModel):
    """Standard job submission response"""
    success: bool = True
    job_id: str
    status: str = "queued"  # queued, running, completed, failed
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class JobStatusResponse(BaseModel):
    """Standard job status response"""
    job_id: str
    status: str  # queued, running, completed, failed
    progress: Optional[float] = None  # 0.0 to 1.0
    result: Optional[Any] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


class SimulationResult(BaseModel):
    """Standardized simulation result"""
    # Timing
    freq: float = Field(..., description="Frequency in MHz")
    delay: float = Field(..., description="Propagation delay in ns")
    
    # Power
    dynamic_power: float = Field(..., description="Dynamic power in mW")
    static_power: float = Field(..., description="Static power in mW")
    total_power: Optional[float] = None
    
    # Conditions
    corner: str
    vdd: float
    temp: int
    
    # Optional advanced metrics
    energy_per_cycle: Optional[float] = None
    power_delay_product: Optional[float] = None
    power_delay_product_squared: Optional[float] = None
    
    # Metadata
    tech_node: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class OptimizationResult(BaseModel):
    """Standardized optimization result"""
    optimized_params: Dict[str, float] = Field(..., description="Optimized device parameters")
    
    # Predictions if ML was used
    predicted_metrics: Optional[SimulationResult] = None
    
    # Confidence metrics
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Confidence in predictions 0-1")
    
    # Comparison with baseline
    baseline_metrics: Optional[SimulationResult] = None
    improvement_percent: Optional[float] = None  # Relative improvement
    
    # Optimization metadata
    algorithm: str  # "ada", "ml", "hybrid"
    iterations: Optional[int] = None
    execution_time_ms: Optional[int] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ValidationResult(BaseModel):
    """Standardized validation result"""
    is_valid: bool
    checks_passed: int
    checks_total: int
    errors: List[str] = []
    warnings: List[str] = []
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PaginatedResponse(BaseModel):
    """Standardized paginated response"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# ============ Helper Functions ============


def create_response(
    success: bool,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized API response"""
    return {
        "success": success,
        "data": data,
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
    }


def create_job_response(
    job_id: str,
    status: str = "queued",
) -> Dict[str, Any]:
    """Create a standardized job submission response"""
    return {
        "success": True,
        "job_id": job_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_job_status_response(
    job_id: str,
    status: str,
    progress: Optional[float] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
    completed_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized job status response"""
    return {
        "job_id": job_id,
        "status": status,
        "progress": progress,
        "result": result,
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
        "completed_at": completed_at,
    }


def normalize_simulation_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize simulation results to standard format
    
    Handles various result formats from different simulators and converts
    them to the standardized format for consistent consumption.
    """
    normalized = {
        "freq": float(raw_result.get("freq") or raw_result.get("frequency", 0)),
        "delay": float(raw_result.get("delay") or raw_result.get("propagation_delay", 0)),
        "dynamic_power": float(raw_result.get("dynamic_power") or raw_result.get("pdyn", 0)),
        "static_power": float(raw_result.get("static_power") or raw_result.get("pstatic", 0)),
        "corner": str(raw_result.get("corner", "tt")),
        "vdd": float(raw_result.get("vdd", 1.2)),
        "temp": int(raw_result.get("temp", 25)),
        "tech_node": int(raw_result.get("tech_node", 5)),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Set total power if not present
    if normalized["dynamic_power"] + normalized["static_power"] > 0:
        normalized["total_power"] = normalized["dynamic_power"] + normalized["static_power"]
    
    # Calculate derived metrics if possible
    if normalized["freq"] > 0 and normalized["total_power"]:
        normalized["power_delay_product"] = normalized["total_power"] * (1 / normalized["freq"])
        normalized["energy_per_cycle"] = normalized["total_power"] / normalized["freq"]
    
    return normalized


def normalize_optimization_result(raw_result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize optimization results to standard format"""
    return {
        "optimized_params": raw_result.get("optimized_params", {}),
        "predicted_metrics": raw_result.get("predicted_metrics"),
        "confidence_score": raw_result.get("confidence_score"),
        "baseline_metrics": raw_result.get("baseline_metrics"),
        "improvement_percent": raw_result.get("improvement_percent"),
        "algorithm": raw_result.get("algorithm", "ada"),
        "iterations": raw_result.get("iterations"),
        "execution_time_ms": raw_result.get("execution_time_ms"),
        "timestamp": datetime.utcnow().isoformat(),
    }


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """Create a standardized paginated response"""
    total_pages = (total + page_size - 1) // page_size
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1,
    }
