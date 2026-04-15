"""
NSGA-II API Integration Guide

Quick reference for integrating the upgraded NSGA-II optimizer
into FastAPI routes and client applications.
"""

# ============================================================================
# 1. FASTAPI ROUTE INTEGRATION
# ============================================================================

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json
from app.nsga2_optimizer import run_optimization

router = APIRouter(prefix="/api/v1/optimize", tags=["Optimization"])


class NSGAIIRequest(BaseModel):
    """Request body for NSGA-II optimization."""
    population_size: int = Field(100, ge=10, le=500, description="GA population size")
    generations: int = Field(50, ge=5, le=200, description="Number of evolutionary generations")
    freq_min: float = Field(0.0, ge=0.0, le=20.0, description="Minimum frequency constraint (GHz)")
    power_max: float = Field(1000.0, ge=0.01, le=10000.0, description="Maximum power constraint (mW)")
    seed: int = Field(42, description="Random seed for reproducibility")


class CircuitSolution(BaseModel):
    """A single circuit solution."""
    wn: float
    wp: float
    vdd: float
    power: float
    frequency: float
    delay: float


class NSGAIIResponse(BaseModel):
    """Response from NSGA-II optimization."""
    success: bool
    solutions: List[CircuitSolution]
    metrics: Dict[str, Any]


@router.post("/nsga2", response_model=NSGAIIResponse)
async def nsga2_optimize(req: NSGAIIRequest):
    """
    Run NSGA-II multi-objective optimization.
    
    Find Pareto-optimal CMOS circuit designs that trade off:
    - Power consumption (minimize)
    - Operating frequency (maximize)
    
    With constraints on minimum frequency and maximum power.
    
    **Example**:
    ```
    POST /api/v1/optimize/nsga2
    {
        "population_size": 100,
        "generations": 50,
        "freq_min": 2.0,
        "power_max": 50.0,
        "seed": 42
    }
    ```
    
    **Response**:
    ```
    {
        "success": true,
        "solutions": [
            {
                "wn": 0.5,
                "wp": 0.543,
                "vdd": 1.001,
                "power": 0.686,
                "frequency": 15.0,
                "delay": 0.202
            },
            ...
        ],
        "metrics": {
            "execution_time": 0.51,
            "hypervolume": 10.13,
            "spread": 0.0,
            "pareto_front_size": 1
        }
    }
    ```
    """
    try:
        # Run optimization
        pf, metrics = run_optimization(
            population_size=req.population_size,
            generations=req.generations,
            freq_min=req.freq_min,
            power_max=req.power_max,
            seed=req.seed,
            verbose=False
        )
        
        # Convert to response format
        solutions = [
            CircuitSolution(
                wn=sol.parameters.wn,
                wp=sol.parameters.wp,
                vdd=sol.parameters.vdd,
                power=sol.performance.power,
                frequency=sol.performance.frequency,
                delay=sol.performance.delay
            )
            for sol in pf
        ]
        
        return NSGAIIResponse(
            success=True,
            solutions=solutions,
            metrics={
                "execution_time": metrics.execution_time,
                "hypervolume": metrics.hypervolume,
                "spread": metrics.spread,
                "pareto_front_size": len(pf),
                "generations": metrics.generations,
                "population_size": metrics.population_size,
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Optimization failed: {str(e)}"
        )


@router.post("/nsga2/fast", response_model=NSGAIIResponse)
async def nsga2_fast():
    """
    Quick NSGA-II optimization (pre-configured for speed).
    
    Uses: 50 population × 20 generations (~0.1s execution)
    """
    pf, metrics = run_optimization(
        population_size=50,
        generations=20,
        seed=42,
        verbose=False
    )
    
    solutions = [
        CircuitSolution(
            wn=sol.parameters.wn,
            wp=sol.parameters.wp,
            vdd=sol.parameters.vdd,
            power=sol.performance.power,
            frequency=sol.performance.frequency,
            delay=sol.performance.delay
        )
        for sol in pf
    ]
    
    return NSGAIIResponse(
        success=True,
        solutions=solutions,
        metrics={
            "execution_time": metrics.execution_time,
            "pareto_front_size": len(pf),
        }
    )


@router.post("/nsga2/constrained", response_model=NSGAIIResponse)
async def nsga2_constrained(
    freq_min: float = 2.0,
    power_max: float = 50.0
):
    """
    Constrained NSGA-II optimization.
    
    Find designs meeting frequency and power requirements.
    
    **Parameters**:
    - freq_min: Minimum frequency in GHz (default 2.0)
    - power_max: Maximum power in mW (default 50.0)
    """
    pf, metrics = run_optimization(
        population_size=100,
        generations=50,
        freq_min=freq_min,
        power_max=power_max,
        seed=42,
        verbose=False
    )
    
    solutions = [
        CircuitSolution(
            wn=sol.parameters.wn,
            wp=sol.parameters.wp,
            vdd=sol.parameters.vdd,
            power=sol.performance.power,
            frequency=sol.performance.frequency,
            delay=sol.performance.delay
        )
        for sol in pf
    ]
    
    # Verify constraints
    feasible_count = sum(
        1 for sol in pf
        if sol.performance.frequency >= freq_min and sol.performance.power <= power_max
    )
    
    return NSGAIIResponse(
        success=True,
        solutions=solutions,
        metrics={
            "execution_time": metrics.execution_time,
            "pareto_front_size": len(pf),
            "feasible_count": feasible_count,
            "constraints": {
                "freq_min_ghz": freq_min,
                "power_max_mw": power_max
            }
        }
    )


# ============================================================================
# 2. PYTHON CLIENT USAGE
# ============================================================================

"""
Example client code for calling the API:

import requests
import json

BASE_URL = "http://localhost:8000/api/v1/optimize"

# 1. Standard optimization
response = requests.post(
    f"{BASE_URL}/nsga2",
    json={
        "population_size": 100,
        "generations": 50,
        "freq_min": 0.0,
        "power_max": 1000.0,
        "seed": 42
    }
)

result = response.json()
print(f"Found {len(result['solutions'])} Pareto-optimal solutions")
print(f"Execution time: {result['metrics']['execution_time']:.2f}s")

# 2. Quick optimization
response = requests.post(f"{BASE_URL}/nsga2/fast")
print(response.json())

# 3. Constrained optimization
response = requests.post(
    f"{BASE_URL}/nsga2/constrained",
    params={"freq_min": 2.0, "power_max": 50.0}
)

result = response.json()
print(f"Feasible designs: {result['metrics']['feasible_count']}")
"""


# ============================================================================
# 3. INTEGRATION WITH EXISTING ROUTES
# ============================================================================

"""
Add to main app.py:

from app.api.nsga2_routes import router as nsga2_router

app.include_router(nsga2_router)

This automatically exposes:
- POST /api/v1/optimize/nsga2
- POST /api/v1/optimize/nsga2/fast
- POST /api/v1/optimize/nsga2/constrained
"""


# ============================================================================
# 4. COMMAND LINE USAGE
# ============================================================================

"""
Run optimizer directly from CLI:

# Basic usage
python -m app.nsga2_optimizer

# With constraints
python -c "
from app.nsga2_optimizer import run_optimization
pf, m = run_optimization(
    population_size=100,
    generations=50,
    freq_min=2.0,
    power_max=50.0
)
print(f'Solutions: {len(pf)}')
print(f'Time: {m.execution_time:.2f}s')
"
"""


# ============================================================================
# 5. PERFORMANCE TUNING
# ============================================================================

"""
Configuration guide:

FAST (for UI responsiveness) - ~0.1s:
- population = 50
- generations = 20
- Good for: Interactive dashboards, real-time feedback

BALANCED (default) - ~0.5s:
- population = 100
- generations = 50
- Good for: Most applications

THOROUGH (high quality) - ~2-5s:
- population = 200
- generations = 100
- Good for: Final designs, offline analysis

PRODUCTION (fixed) - ~1s:
- population = 150
- generations = 40
- Good for: Standard deployments

For FastAPI, wrap in async:

@app.post("/optimize")
async def optimize():
    # Use thread pool for long operations
    loop = asyncio.get_event_loop()
    pf, m = await loop.run_in_executor(
        None,
        run_optimization,
        100, 50, False, 42, 0.0, 1000.0, False
    )
    return {"solutions": len(pf), "time": m.execution_time}
"""

# ============================================================================
# 6. ERROR HANDLING
# ============================================================================

"""
Common errors and solutions:

RuntimeError: DEAP not installed
→ pip install deap

ValueError: Population size too small
→ Use population_size >= 10

ValueError: Constraints too tight
→ Relax freq_min and power_max

TimeoutError: Takes too long
→ Reduce population_size or generations
→ Or run in background task
"""

# ============================================================================
# 7. EXPORT FORMATS
# ============================================================================

"""
JSON export:

import json
from app.nsga2_optimizer import run_optimization

pf, metrics = run_optimization()

output = {
    "timestamp": metrics.timestamp,
    "pareto_front": [
        {
            "wn": sol.parameters.wn,
            "wp": sol.parameters.wp,
            "vdd": sol.parameters.vdd,
            "power": sol.performance.power,
            "frequency": sol.performance.frequency,
            "delay": sol.performance.delay
        }
        for sol in pf
    ],
    "metrics": {
        "execution_time": metrics.execution_time,
        "hypervolume": metrics.hypervolume,
        "spread": metrics.spread,
        "pareto_front_size": len(pf),
    }
}

with open("pareto_front.json", "w") as f:
    json.dump(output, f, indent=2)
"""
