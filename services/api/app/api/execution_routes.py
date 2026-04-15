"""
FastAPI routes for execution-based AI optimization system.

Exposes the execution engine as REST endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
import logging

from execution_engine import ExecutionEngine, OptimizationObjective

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/execution",
    tags=["Execution Engine"]
)

# Request/Response models
class ExecutionRequest(BaseModel):
    """Natural language optimization request"""
    request: str = Field(..., description="Natural language optimization request")
    example: Optional[str] = Field(
        None,
        description="Examples: 'optimize for low power under 1GHz', 'maximize frequency with power budget 20mW'"
    )


class CircuitDesignOutput(BaseModel):
    """Circuit design parameters and performance"""
    wn: float = Field(..., description="NMOS transistor width (µm)")
    wp: float = Field(..., description="PMOS transistor width (µm)")
    vdd: float = Field(..., description="Supply voltage (V)")
    power: float = Field(..., description="Power consumption (mW)")
    frequency: float = Field(..., description="Operating frequency (GHz)")
    efficiency: float = Field(..., description="Efficiency (GHz/mW)")


class OptimizationSolutions(BaseModel):
    """Best solutions from optimization"""
    best_power: Optional[CircuitDesignOutput] = Field(None, description="Design with lowest power")
    best_frequency: Optional[CircuitDesignOutput] = Field(None, description="Design with highest frequency")
    best_efficiency: Optional[CircuitDesignOutput] = Field(None, description="Design with best efficiency")


class ConstraintInfo(BaseModel):
    """Extracted constraints"""
    max_power: Optional[float] = Field(None, description="Maximum power budget (mW)")
    min_frequency: Optional[float] = Field(None, description="Minimum frequency (GHz)")
    max_frequency: Optional[float] = Field(None, description="Maximum frequency (GHz)")
    min_efficiency: Optional[float] = Field(None, description="Minimum efficiency (GHz/mW)")


class OptimizationInfo(BaseModel):
    """Optimization execution details"""
    population_size: int = Field(..., description="EA population size")
    generations: int = Field(..., description="EA generations")
    total_solutions: int = Field(..., description="Total solutions in Pareto front")
    valid_solutions: int = Field(..., description="Solutions meeting all constraints")


class ExecutionResponse(BaseModel):
    """Response from optimization execution"""
    status: str = Field(..., description="'success' or 'error'")
    request: str = Field(..., description="Original request")
    objectives: List[str] = Field(..., description="Extracted optimization objectives")
    constraints: ConstraintInfo = Field(..., description="Extracted constraints")
    optimization: OptimizationInfo = Field(..., description="Optimization execution details")
    solutions: Optional[OptimizationSolutions] = Field(None, description="Best solutions found")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = Field(None, description="Error message if status is 'error'")


# Initialize execution engine
execution_engine = ExecutionEngine()


@router.post("/execute", response_model=ExecutionResponse, summary="Execute natural language optimization")
async def execute_optimization(req: ExecutionRequest) -> ExecutionResponse:
    """
    Execute optimization based on natural language request.
    
    **Steps:**
    1. Parse natural language input
    2. Extract optimization constraints and objectives
    3. Call NSGA-II multi-objective optimizer
    4. Return Pareto front solutions
    
    **Example requests:**
    - "optimize for low power under 1GHz"
    - "maximize frequency with power budget 20mW"
    - "balance power and efficiency, keep voltage low"
    - "high performance design, frequency at least 1.5 GHz"
    
    **Returns:**
    - Extracted objectives and constraints
    - Best solutions for power, frequency, and efficiency
    - Optimization execution metrics
    """
    if not req.request.strip():
        raise HTTPException(status_code=422, detail="Request cannot be empty")
    
    try:
        logger.info(f"Executing optimization request: {req.request}")
        result = execution_engine.execute(req.request)
        
        if result['status'] == 'error':
            raise HTTPException(
                status_code=500,
                detail=f"Optimization execution failed: {result.get('error', 'Unknown error')}"
            )
        
        # Format response
        solutions = None
        if 'solutions' in result:
            sols = result['solutions']
            solutions = OptimizationSolutions(
                best_power=CircuitDesignOutput(**sols['best_power']) if 'best_power' in sols else None,
                best_frequency=CircuitDesignOutput(**sols['best_frequency']) if 'best_frequency' in sols else None,
                best_efficiency=CircuitDesignOutput(**sols['best_efficiency']) if 'best_efficiency' in sols else None,
            )
        
        response = ExecutionResponse(
            status=result['status'],
            request=result['request'],
            objectives=result['objectives'],
            constraints=ConstraintInfo(**result['constraints']),
            optimization=OptimizationInfo(**result['optimization']),
            solutions=solutions,
        )
        
        logger.info(f"Optimization succeeded: {response.optimization.valid_solutions} valid solutions found")
        return response
        
    except Exception as e:
        logger.error(f"Execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supported-keywords", summary="Get list of supported keywords")
async def get_supported_keywords() -> Dict:
    """
    Get list of natural language keywords supported by the parser.
    
    Helps users formulate effective optimization requests.
    """
    return {
        "power_keywords": [
            "low power", "reduced power", "minimal power",
            "power under X mW", "power below X mW",
            "keep power under X", "maintain power under X"
        ],
        "frequency_keywords": [
            "high frequency", "maximum frequency", "peak frequency",
            "frequency under X GHz", "up to X GHz",
            "at least X GHz", "minimum X GHz frequency"
        ],
        "efficiency_keywords": [
            "high efficiency", "maximum efficiency", "improve efficiency",
            "efficiency above X", "efficiency at least X"
        ],
        "transistor_keywords": [
            "small transistor", "narrow gate width",
            "large transistor", "wide gate width", "thick transistor"
        ],
        "voltage_keywords": [
            "low voltage", "reduced voltage", "minimal voltage",
            "high voltage", "maximum voltage",
            "voltage = X V", "voltage is X V"
        ],
        "examples": [
            "optimize for low power under 1GHz",
            "maximize frequency with power constraint 20mW",
            "high efficiency design, voltage at 2.8V",
            "balance power and efficiency, keep voltage low",
            "performance-critical, frequency at least 1.5 GHz"
        ]
    }


@router.get("/health", summary="Health check")
async def health_check() -> Dict:
    """Check execution engine health"""
    return {
        "status": "healthy",
        "engine": "execution-based-ai",
        "capabilities": [
            "natural_language_parsing",
            "constraint_extraction",
            "nsga2_optimization",
            "pareto_front_derivation"
        ],
        "timestamp": datetime.utcnow()
    }
