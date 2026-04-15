"""
FastAPI endpoints for NSGA-II multi-objective optimization.

Exposes:
- POST /api/v1/nsga2/optimize - Run NSGA-II optimization
- GET /api/v1/nsga2/health - Health check
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import logging
from datetime import datetime

try:
    from app.nsga2_optimizer import (
        NSGAII_Optimizer, run_optimization, ParetoSolution, OptimizationMetrics
    )
    NSGA2_AVAILABLE = True
except ImportError:
    NSGA2_AVAILABLE = False

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/nsga2", tags=["nsga2-optimization"])


# ============================================================================
# Request/Response Models
# ============================================================================


class OptimizationRequest(BaseModel):
    """Request body for optimization."""
    
    population_size: int = Field(default=50, ge=10, le=1000, description="Population size")
    generations: int = Field(default=30, ge=5, le=500, description="Number of generations")
    use_ml: bool = Field(default=False, description="Use ML model for prediction")
    seed: int = Field(default=42, ge=0, description="Random seed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "population_size": 50,
                "generations": 30,
                "use_ml": False,
                "seed": 42
            }
        }


class CircuitParametersOutput(BaseModel):
    """Circuit parameters."""
    wn: float = Field(..., description="NMOS width (µm)")
    wp: float = Field(..., description="PMOS width (µm)")
    vdd: float = Field(..., description="Supply voltage (V)")


class CircuitPerformanceOutput(BaseModel):
    """Circuit performance metrics."""
    frequency: float = Field(..., description="Operating frequency (GHz)")
    power: float = Field(..., description="Power consumption (mW)")
    delay: float = Field(..., description="Propagation delay (ns)")
    efficiency: float = Field(..., description="Energy efficiency (GHz/mW)")


class ParetoSolutionOutput(BaseModel):
    """A solution on the Pareto front."""
    parameters: CircuitParametersOutput
    performance: CircuitPerformanceOutput
    rank: int = Field(default=1, description="Pareto rank")


class OptimizationMetricsOutput(BaseModel):
    """Optimization metrics."""
    generations: int
    population_size: int
    execution_time: float
    pareto_front_size: int
    hypervolume: float
    spread: float
    timestamp: str


class OptimizationResponse(BaseModel):
    """Response from optimization."""
    status: str = Field(..., description="Optimization status")
    pareto_front: List[ParetoSolutionOutput] = Field(..., description="Pareto-optimal solutions")
    metrics: OptimizationMetricsOutput = Field(..., description="Optimization metrics")
    best_solutions: Dict = Field(..., description="Best solutions for each objective")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("/optimize", response_model=OptimizationResponse, summary="Run NSGA-II optimization")
async def optimize(request: OptimizationRequest) -> OptimizationResponse:
    """
    Run NSGA-II multi-objective optimization.
    
    Objectives:
    - Minimize: Power consumption
    - Maximize: Operating frequency
    
    Returns:
    - Complete Pareto front
    - Optimization metrics
    - Best solutions for individual objectives
    
    Example:
        ```json
        {
            "population_size": 50,
            "generations": 30,
            "use_ml": false,
            "seed": 42
        }
        ```
    """
    if not NSGA2_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="NSGA-II optimizer not available. Install DEAP: pip install deap"
        )
    
    try:
        logger.info(f"Starting NSGA-II optimization: pop={request.population_size}, "
                   f"gen={request.generations}, ml={request.use_ml}")
        
        # Run optimization
        pareto_front, metrics = run_optimization(
            population_size=request.population_size,
            generations=request.generations,
            use_ml=request.use_ml,
            seed=request.seed,
            verbose=True
        )
        
        # Convert to output models
        pareto_output = [
            ParetoSolutionOutput(
                parameters=CircuitParametersOutput(
                    wn=sol.parameters.wn,
                    wp=sol.parameters.wp,
                    vdd=sol.parameters.vdd
                ),
                performance=CircuitPerformanceOutput(
                    frequency=sol.performance.frequency,
                    power=sol.performance.power,
                    delay=sol.performance.delay,
                    efficiency=sol.performance.efficiency
                ),
                rank=sol.rank
            )
            for sol in pareto_front
        ]
        
        metrics_output = OptimizationMetricsOutput(
            generations=metrics.generations,
            population_size=metrics.population_size,
            execution_time=metrics.execution_time,
            pareto_front_size=metrics.pareto_front_size,
            hypervolume=metrics.hypervolume,
            spread=metrics.spread,
            timestamp=metrics.timestamp
        )
        
        # Find best solutions for each objective
        best_power = min(pareto_front, key=lambda s: s.performance.power) if pareto_front else None
        best_frequency = max(pareto_front, key=lambda s: s.performance.frequency) if pareto_front else None
        best_efficiency = max(pareto_front, key=lambda s: s.performance.efficiency) if pareto_front else None
        
        best_solutions = {}
        if best_power:
            best_solutions["best_power"] = {
                "wn": best_power.parameters.wn,
                "wp": best_power.parameters.wp,
                "vdd": best_power.parameters.vdd,
                "power": best_power.performance.power,
                "frequency": best_power.performance.frequency
            }
        if best_frequency:
            best_solutions["best_frequency"] = {
                "wn": best_frequency.parameters.wn,
                "wp": best_frequency.parameters.wp,
                "vdd": best_frequency.parameters.vdd,
                "power": best_frequency.performance.power,
                "frequency": best_frequency.performance.frequency
            }
        if best_efficiency:
            best_solutions["best_efficiency"] = {
                "wn": best_efficiency.parameters.wn,
                "wp": best_efficiency.parameters.wp,
                "vdd": best_efficiency.parameters.vdd,
                "power": best_efficiency.performance.power,
                "frequency": best_efficiency.performance.frequency,
                "efficiency": best_efficiency.performance.efficiency
            }
        
        return OptimizationResponse(
            status="success",
            pareto_front=pareto_output,
            metrics=metrics_output,
            best_solutions=best_solutions
        )
    
    except Exception as e:
        logger.error(f"Optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", summary="Health check")
async def health_check():
    """Check if NSGA-II optimizer is available."""
    return {
        "status": "healthy" if NSGA2_AVAILABLE else "unavailable",
        "nsga2_available": NSGA2_AVAILABLE,
        "deap_requirement": "deap>=1.4.1",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/compare", summary="Compare two designs")
async def compare_designs(
    design1: CircuitParametersOutput,
    design2: CircuitParametersOutput
):
    """
    Compare two circuit designs.
    
    Returns performance metrics for both designs.
    """
    from app.nsga2_optimizer import PerformancePredictor, CircuitParameters
    
    try:
        predictor = PerformancePredictor(use_ml=False)
        
        params1 = CircuitParameters(wn=design1.wn, wp=design1.wp, vdd=design1.vdd)
        params2 = CircuitParameters(wn=design2.wn, wp=design2.wp, vdd=design2.vdd)
        
        perf1 = predictor.predict(params1)
        perf2 = predictor.predict(params2)
        
        return {
            "design1": {
                "parameters": {"wn": design1.wn, "wp": design1.wp, "vdd": design1.vdd},
                "performance": {
                    "frequency": perf1.frequency,
                    "power": perf1.power,
                    "delay": perf1.delay,
                    "efficiency": perf1.efficiency
                }
            },
            "design2": {
                "parameters": {"wn": design2.wn, "wp": design2.wp, "vdd": design2.vdd},
                "performance": {
                    "frequency": perf2.frequency,
                    "power": perf2.power,
                    "delay": perf2.delay,
                    "efficiency": perf2.efficiency
                }
            },
            "comparison": {
                "frequency_ratio": perf2.frequency / perf1.frequency if perf1.frequency > 0 else 0,
                "power_ratio": perf2.power / perf1.power if perf1.power > 0 else 0,
                "efficiency_ratio": perf2.efficiency / perf1.efficiency if perf1.efficiency > 0 else 0
            }
        }
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info", summary="Get optimizer information")
async def optimizer_info():
    """Get information about NSGA-II optimizer."""
    return {
        "name": "NSGA-II Multi-Objective Optimizer",
        "description": "Non-dominated Sorting Genetic Algorithm II for CMOS circuit optimization",
        "objectives": [
            {"name": "Power", "type": "minimize", "unit": "mW"},
            {"name": "Frequency", "type": "maximize", "unit": "GHz"}
        ],
        "parameters": [
            {"name": "WN", "description": "NMOS width", "unit": "µm", "range": [0.5, 10.0]},
            {"name": "WP", "description": "PMOS width", "unit": "µm", "range": [0.5, 10.0]},
            {"name": "VDD", "description": "Supply voltage", "unit": "V", "range": [1.0, 5.0]}
        ],
        "algorithm": "NSGA-II (DEAP implementation)",
        "outputs": ["Pareto front", "Optimization metrics", "Best solutions"]
    }


# Export router
__all__ = ["router"]
