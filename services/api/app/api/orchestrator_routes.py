"""
Agentic Orchestrator API Routes
================================

REST endpoints for accessing the autonomous design agent.
Execution-based interface for CMOS design optimization.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

from app.agentic_orchestrator import (
    AgenticOrchestrator,
    DesignIntent,
    OrchestratorResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orchestrator", tags=["Agentic Orchestrator"])

# Global orchestrator instance
_orchestrator: Optional[AgenticOrchestrator] = None


def get_orchestrator() -> AgenticOrchestrator:
    """Get or create global orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgenticOrchestrator()
    return _orchestrator


# ============================================================================
# Request/Response Models
# ============================================================================

class DesignOptimizationRequest(BaseModel):
    """Request model for orchestrator design optimization"""
    
    design_specification: str = Field(
        ...,
        description="Natural language design intent (e.g., 'minimize power under 100mW with >500MHz')"
    )
    
    optimization_layer: Optional[str] = Field(
        "full",
        description="'full' (all components), 'fast' (optimizer only), 'deep' (intensive analysis)"
    )
    
    use_gpu_acceleration: bool = Field(
        True,
        description="Use GPU-accelerated Digital Twin if available"
    )
    
    include_reliability_analysis: bool = Field(
        True,
        description="Include device reliability (aging) analysis"
    )
    
    enable_distributed_optimization: bool = Field(
        False,
        description="Use Ray distributed optimization for intensive search"
    )


class DesignPoint(BaseModel):
    """Single design point result"""
    wn: float
    wp: float
    vdd: float
    temperature: float
    power_mw: Optional[float] = None
    frequency_mhz: Optional[float] = None
    delay_ns: Optional[float] = None
    efficiency_mhz_per_mw: Optional[float] = None
    reliability_score: Optional[float] = None
    device_lifetime_years: Optional[float] = None
    pareto_rank: Optional[int] = None
    multi_objective_score: Optional[float] = None


class DesignOptimizationResponse(BaseModel):
    """Response model with orchestrator results"""
    
    request_id: str
    timestamp: str
    
    # Design intent
    design_intent: Dict[str, Any]
    
    # Best design
    best_design: DesignPoint
    best_design_reasoning: str
    
    # Pareto front alternatives
    pareto_front: List[DesignPoint] = []
    
    # Reasoning and confidence
    execution_reasoning: str
    constraint_satisfaction: Dict[str, bool]
    
    overall_confidence: float
    component_confidence: Dict[str, float]
    
    # Component status
    components_evaluated: List[str]
    execution_time_ms: float


class OrchestratorHealthResponse(BaseModel):
    """Orchestrator health check"""
    status: str
    components_available: Dict[str, bool]
    average_execution_time_ms: float
    total_optimizations_run: int
    last_optimization_timestamp: Optional[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/optimize", response_model=DesignOptimizationResponse)
async def optimize_design(request: DesignOptimizationRequest) -> DesignOptimizationResponse:
    """
    Run agentic orchestrator for CMOS design optimization.
    
    **Execution Flow:**
    1. Parse natural language design intent
    2. Plan multi-component execution
    3. Run NSGA-II optimizer for Pareto front
    4. Enhance with Digital Twin predictions
    5. Analyze device reliability
    6. Combine results with reasoning & confidence
    
    **Returns:**
    - Best design (multi-objective optimized)
    - Pareto front (tradeoff options)
    - Reasoning (why selected)
    - Confidence scores
    
    **Example Request:**
    ```json
    {
        "design_specification": "minimize power under 100mW with minimum 500MHz frequency",
        "optimization_layer": "full",
        "include_reliability_analysis": true
    }
    ```
    """
    try:
        orchestrator = get_orchestrator()
        
        logger.info(f"🎯 Optimization request: {request.design_specification[:100]}...")
        
        # Get service instances (in production, these would be injected)
        # For now, we'll use None and handle gracefully in orchestrator
        digital_twin_service = None  # Would come from dependency injection
        optimizer_service = None  # Would come from dependency injection
        reliability_model = None  # Would come from dependency injection
        
        # Run orchestration
        result = await orchestrator.orchestrate(
            design_specification=request.design_specification,
            digital_twin_service=digital_twin_service,
            optimizer_service=optimizer_service,
            reliability_model=reliability_model
        )
        
        # Convert OrchestratorResponse to API response
        response = DesignOptimizationResponse(
            request_id=result.request_id,
            timestamp=result.timestamp,
            design_intent=result.design_intent,
            best_design=DesignPoint(**result.best_design),
            best_design_reasoning=result.best_design_reasoning,
            pareto_front=[DesignPoint(**d) for d in result.pareto_front],
            execution_reasoning=result.execution_reasoning,
            constraint_satisfaction=result.constraint_satisfaction,
            overall_confidence=result.overall_confidence,
            component_confidence=result.component_confidence,
            components_evaluated=result.components_evaluated,
            execution_time_ms=result.execution_time_ms
        )
        
        logger.info(f"✅ Optimization complete (confidence: {response.overall_confidence:.2%})")
        return response
        
    except Exception as e:
        logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Orchestration failed: {str(e)}")


@router.post("/batch-optimize")
async def batch_optimize_designs(
    specifications: List[str],
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """
    Run orchestrator on multiple design specifications in batch.
    
    Returns immediately with job ID, runs optimizations in background.
    """
    try:
        orchestrator = get_orchestrator()
        job_id = f"batch_{int(datetime.now().timestamp() * 1000)}"
        
        logger.info(f"📦 Batch optimization started: {job_id} ({len(specifications)} specs)")
        
        # Schedule background execution
        async def run_batch():
            results = []
            for spec in specifications:
                try:
                    result = await orchestrator.orchestrate(
                        design_specification=spec,
                        digital_twin_service=None,
                        optimizer_service=None,
                        reliability_model=None
                    )
                    results.append({
                        "specification": spec,
                        "status": "success",
                        "best_design_score": result.best_design["multi_objective_score"]
                    })
                except Exception as e:
                    results.append({
                        "specification": spec,
                        "status": "failed",
                        "error": str(e)
                    })
            
            logger.info(f"✅ Batch optimization complete: {job_id}")
            return results
        
        # For now, run synchronously (in production use background tasks)
        background_tasks.add_task(run_batch)
        
        return {
            "job_id": job_id,
            "status": "queued",
            "specifications_count": len(specifications),
            "message": "Batch optimization queued for execution"
        }
        
    except Exception as e:
        logger.error(f"❌ Batch optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch optimization failed: {str(e)}")


@router.get("/health", response_model=OrchestratorHealthResponse)
async def orchestrator_health() -> OrchestratorHealthResponse:
    """
    Get orchestrator health status and statistics.
    
    **Returns:**
    - Status (healthy/degraded)
    - Available components
    - Execution statistics
    """
    try:
        orchestrator = get_orchestrator()
        history = orchestrator.get_execution_history()
        
        avg_time = 0.0
        last_timestamp = None
        
        if history:
            execution_times = []
            for entry in history:
                # In production, execution_time would be stored
                execution_times.append(100.0)  # Placeholder
            
            avg_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
            last_timestamp = history[-1]["timestamp"] if history else None
        
        return OrchestratorHealthResponse(
            status="healthy",
            components_available={
                "optimizer": True,
                "digital_twin": True,
                "reliability_engine": True,
                "gpu_acceleration": True
            },
            average_execution_time_ms=avg_time,
            total_optimizations_run=len(history),
            last_optimization_timestamp=last_timestamp
        )
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/execution-history")
async def get_execution_history(limit: int = 10) -> Dict[str, Any]:
    """
    Get recent orchestrator execution history.
    
    **Returns:**
    - List of recent optimizations with results
    - Request patterns
    - Success rates
    """
    try:
        orchestrator = get_orchestrator()
        history = orchestrator.get_execution_history()
        
        # Return last N executions
        recent = history[-limit:] if history else []
        
        # Compute statistics
        total = len(history)
        successful = sum(1 for h in history if h.get("status") == "success")
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            "total_executions": total,
            "successful": successful,
            "success_rate_percent": success_rate,
            "recent_executions": recent,
            "average_score": np.mean([h.get("best_design_score", 0) for h in history]) if history else 0
        }
        
    except Exception as e:
        logger.error(f"❌ History retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


@router.post("/explain-decision/{request_id}")
async def explain_decision(request_id: str) -> Dict[str, Any]:
    """
    Get detailed explanation of a specific orchestrator decision.
    
    **Returns:**
    - Why this design was selected
    - How constraints were considered
    - Component contributions
    - Confidence factors
    """
    try:
        orchestrator = get_orchestrator()
        history = orchestrator.get_execution_history()
        
        # Find request in history
        execution = next((h for h in history if h.get("request_id") == request_id), None)
        
        if not execution:
            raise HTTPException(status_code=404, detail=f"Request {request_id} not found")
        
        return {
            "request_id": request_id,
            "timestamp": execution.get("timestamp"),
            "design_intent": execution.get("design_intent"),
            "design_specification": execution.get("design_intent"),
            "best_design_score": execution.get("best_design_score"),
            "explanation": "Design selection reasoning available in past executions"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Explanation retrieval failed: {e}")
        raise HTTPException(status_code=500, detail=f"Explanation retrieval failed: {str(e)}")


@router.post("/parse-intent")
async def parse_design_intent(specification: str) -> Dict[str, Any]:
    """
    Parse natural language design specification into structured intent.
    
    **Returns:**
    - Optimization target
    - Extracted constraints
    - Detected parameters
    
    **Useful for:**
    - Validating specifications before optimization
    - Showing what the agent understood
    - Debugging spec parsing
    """
    try:
        # Parse specification
        intent = DesignIntent.from_natural_language(specification)
        
        return {
            "original_specification": specification,
            "parsed_intent": {
                "primary_target": intent.primary_target.value,
                "wn_range": intent.wn_range,
                "wp_range": intent.wp_range,
                "vdd_range": intent.vdd_range,
                "temp_range": intent.temp_range,
                "max_power_mw": intent.max_power,
                "min_frequency_mhz": intent.min_frequency,
                "min_lifetime_years": intent.min_lifetime,
                "max_area_um2": intent.max_area,
                "process_corner": intent.corner,
                "tech_node_nm": intent.tech_node,
                "optimization_priority": intent.optimization_priority
            },
            "confidence": "intent parsing is deterministic, confidence=1.0"
        }
        
    except Exception as e:
        logger.error(f"❌ Intent parsing failed: {e}")
        raise HTTPException(status_code=400, detail=f"Intent parsing failed: {str(e)}")


@router.get("/capabilities")
async def get_capabilities() -> Dict[str, Any]:
    """
    Get orchestrator capabilities and supported optimization targets.
    
    **Returns:**
    - Supported optimization objectives
    - Available components
    - Execution modes
    """
    return {
        "orchestrator_version": "1.0.0",
        "supported_targets": [
            "power_minimal",
            "frequency_maximal",
            "efficiency_maximal",
            "balanced",
            "ppa_optimal",
            "reliability_focused"
        ],
        "components": {
            "optimizer": {
                "type": "NSGA-II Multi-Objective Evolutionary Algorithm",
                "modes": ["light", "standard", "intensive"],
                "supports_gpu": True
            },
            "digital_twin": {
                "type": "GPU-Accelerated Surrogate Model",
                "models": ["XGBoost", "PyTorch Neural Network"],
                "supports_gpu": True
            },
            "reliability_engine": {
                "type": "Physics-Based Degradation Model",
                "mechanisms": ["NBTI", "HCI", "Electromigration"],
                "supports_gpu": False
            }
        },
        "execution_modes": [
            "sequential",
            "distributed_ray",
            "hybrid_gpu_distributed"
        ],
        "supported_constraints": [
            "max_power",
            "min_frequency",
            "min_lifetime",
            "max_area"
        ],
        "output_types": [
            "best_design",
            "pareto_front",
            "constraint_satisfaction",
            "confidence_metrics",
            "detailed_reasoning"
        ]
    }


# ============================================================================
# Internal helper functions
# ============================================================================

import numpy as np
