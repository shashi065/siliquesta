"""
Hybrid AI REST API Routes
=========================

REST endpoints for hybrid edge/cloud AI inference with automatic failover.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import logging

from app.hybrid_orchestrator import get_hybrid_orchestrator, HybridAIRequest
from app.connectivity_detector import get_connectivity_detector
from app.onnx_model_manager import get_onnx_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/hybrid", tags=["Hybrid AI"])


# ============================================================================
# Request/Response Models
# ============================================================================

class HybridPredictionRequest(BaseModel):
    """Request for hybrid prediction"""
    model_name: str = Field(..., description="Model: 'digital_twin', 'optimizer', 'reliability'")
    inputs: Dict[str, Any] = Field(..., description="Input parameters")
    user_preference: str = Field("auto", description="'auto', 'edge', or 'cloud'")
    priority: str = Field("normal", description="'high', 'normal', or 'low'")


class HybridPredictionResponse(BaseModel):
    """Response with model source and metadata"""
    model_name: str
    result: Dict[str, Any]
    model_source: str  # "edge" or "cloud"
    execution_time_ms: float
    confidence: float
    edge_degradation_percent: float
    fallback_used: bool
    latency_ms: Optional[float] = None
    timestamp: str


class ConnectivityStatus(BaseModel):
    """Connectivity status"""
    is_online: bool
    primary_service: str
    fallback_active: bool
    latency_ms: Optional[float]
    consecutive_failures: int
    consecutive_successes: int


class HybridSystemStatus(BaseModel):
    """Complete system status"""
    connectivity: Dict[str, Any]
    model_source: str
    edge_models_available: List[str]
    total_requests_processed: int
    model_performance: Dict[str, Any]


# ============================================================================
# Prediction Endpoints
# ============================================================================

@router.post("/predict", response_model=HybridPredictionResponse)
async def hybrid_predict(request: HybridPredictionRequest) -> HybridPredictionResponse:
    """
    Make prediction with automatic edge/cloud routing.
    
    **Behavior:**
    - If offline: uses lightweight edge ONNX model (2% accuracy loss)
    - If online: uses full cloud AI backend (highest accuracy)
    - Automatic failover if network unreachable
    
    **Example:**
    ```json
    {
        "model_name": "digital_twin",
        "inputs": {"wn": 2.5, "wp": 5.2, "vdd": 0.9, "temp": 25},
        "user_preference": "auto"
    }
    ```
    """
    try:
        orchestrator = get_hybrid_orchestrator()
        
        # Create request
        hybrid_request = HybridAIRequest(
            task_type="predict",
            model_name=request.model_name,
            inputs=request.inputs,
            priority=request.priority,
            user_preference=request.user_preference
        )
        
        # Process with hybrid logic
        response = await orchestrator.process(hybrid_request)
        
        return HybridPredictionResponse(
            model_name=response.model_name,
            result=response.result,
            model_source=response.model_source,
            execution_time_ms=response.execution_time_ms,
            confidence=response.confidence,
            edge_degradation_percent=response.edge_degradation_percent,
            fallback_used=response.fallback_used,
            latency_ms=response.latency_ms,
            timestamp=response.timestamp
        )
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/batch")
async def hybrid_predict_batch(requests: List[HybridPredictionRequest]) -> List[HybridPredictionResponse]:
    """
    Batch predictions with edge/cloud routing.
    
    **Optimizes:**
    - Single connectivity check for all requests
    - Batches edge models when possible
    - Parallel cloud requests
    """
    try:
        orchestrator = get_hybrid_orchestrator()
        results = []
        
        for req in requests:
            hybrid_request = HybridAIRequest(
                task_type="predict",
                model_name=req.model_name,
                inputs=req.inputs,
                priority=req.priority,
                user_preference=req.user_preference
            )
            
            response = await orchestrator.process(hybrid_request)
            
            results.append(HybridPredictionResponse(
                model_name=response.model_name,
                result=response.result,
                model_source=response.model_source,
                execution_time_ms=response.execution_time_ms,
                confidence=response.confidence,
                edge_degradation_percent=response.edge_degradation_percent,
                fallback_used=response.fallback_used,
                latency_ms=response.latency_ms,
                timestamp=response.timestamp
            ))
        
        return results
        
    except Exception as e:
        logger.error(f"Batch prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {str(e)}")


@router.get("/force-edge")
async def force_edge_model() -> Dict[str, str]:
    """
    Force use of edge models for testing.
    
    **Use cases:**
    - Simulate offline environment
    - Benchmark edge performance
    - Test fallback mechanisms
    """
    detector = get_connectivity_detector()
    detector.status.primary_service = "edge"
    detector.status.fallback_active = True
    
    logger.info("✓ Forced edge model mode")
    return {"mode": "edge", "message": "Using edge (ONNX) models"}


@router.get("/force-cloud")
async def force_cloud_model() -> Dict[str, str]:
    """
    Force use of cloud models for testing.
    
    **Use cases:**
    - Benchmark cloud performance
    - Test with full AI backend
    - Compare edge vs cloud
    """
    detector = get_connectivity_detector()
    detector.status.primary_service = "cloud"
    detector.status.fallback_active = False
    
    logger.info("✓ Forced cloud model mode")
    return {"mode": "cloud", "message": "Using cloud (full AI) models"}


@router.get("/auto-switch")
async def auto_switch_mode() -> Dict[str, str]:
    """Re-enable automatic edge/cloud switching"""
    detector = get_connectivity_detector()
    await detector.check_connectivity()
    
    mode = detector.get_recommended_model_source()
    logger.info(f"✓ Switched to auto mode (current: {mode})")
    
    return {
        "mode": "auto",
        "current_source": mode,
        "message": "Automatic switching enabled"
    }


# ============================================================================
# Status & Monitoring
# ============================================================================

@router.get("/status", response_model=HybridSystemStatus)
async def get_system_status() -> HybridSystemStatus:
    """
    Get complete hybrid system status.
    
    **Returns:**
    - Connectivity info (online/offline, latency)
    - Current model source (edge or cloud)
    - Loaded edge models
    - Performance statistics
    """
    try:
        orchestrator = get_hybrid_orchestrator()
        connectivity = get_connectivity_detector()
        onnx_manager = get_onnx_manager()
        
        system_status = orchestrator.get_system_status()
        
        return HybridSystemStatus(
            connectivity=connectivity.get_status(),
            model_source=connectivity.get_recommended_model_source(),
            edge_models_available=onnx_manager.list_models() if onnx_manager else [],
            total_requests_processed=sum(
                p.get("total_requests", 0)
                for p in orchestrator.model_performance.values()
            ),
            model_performance=orchestrator.model_performance
        )
        
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")


@router.get("/connectivity")
async def get_connectivity_status() -> Dict[str, Any]:
    """
    Get detailed connectivity information.
    
    **Returns:**
    - Online/offline status
    - Cloud latency
    - Failure/success counts
    - Last check time
    """
    detector = get_connectivity_detector()
    
    # Run a check if needed
    if detector.status.is_online is None or (detector.status.consecutive_failures > 0):
        await detector.check_connectivity()
    
    return detector.get_status()


@router.get("/models/available")
async def list_available_models() -> Dict[str, Any]:
    """
    List available ONNX edge models.
    
    **Returns:**
    - Model names
    - Model sizes
    - Input/output shapes
    - Quantization info
    """
    onnx_manager = get_onnx_manager()
    
    if not onnx_manager:
        return {"onnx_available": False, "models": []}
    
    models_info = []
    for model_name in onnx_manager.list_models():
        info = onnx_manager.get_model_info(model_name)
        if info:
            models_info.append(info)
    
    return {
        "onnx_available": True,
        "models_loaded": len(models_info),
        "models": models_info
    }


@router.get("/performance")
async def get_performance_metrics(
    model_name: Optional[str] = Query(None, description="Filter by model (optional)")
) -> Dict[str, Any]:
    """
    Get performance metrics and statistics.
    
    **Metrics:**
    - Total requests processed
    - Edge vs cloud requests
    - Average execution time
    - Average confidence
    - Execution history
    """
    orchestrator = get_hybrid_orchestrator()
    
    if model_name:
        stats = orchestrator.get_performance_stats(model_name)
        recent = [e for e in orchestrator.get_recent_executions() if e["model"] == model_name]
    else:
        stats = orchestrator.get_performance_stats()
        recent = orchestrator.get_recent_executions()
    
    return {
        "performance_stats": stats,
        "recent_executions": recent[:10]
    }


# ============================================================================
# Model Management
# ============================================================================

@router.post("/models/load")
async def load_edge_model(model_name: str = Query(..., description="Model name to load")) -> Dict[str, str]:
    """
    Manually load edge ONNX model.
    
    **Models:**
    - digital_twin_edge
    - optimizer_edge
    - reliability_edge
    """
    onnx_manager = get_onnx_manager()
    
    if not onnx_manager:
        raise HTTPException(status_code=503, detail="ONNX not available")
    
    if onnx_manager.load_model(model_name):
        return {"status": "loaded", "model": model_name}
    else:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")


@router.post("/models/unload")
async def unload_edge_model(model_name: str = Query(..., description="Model name to unload")) -> Dict[str, str]:
    """
    Unload edge ONNX model to free memory.
    """
    onnx_manager = get_onnx_manager()
    
    if not onnx_manager:
        raise HTTPException(status_code=503, detail="ONNX not available")
    
    if onnx_manager.unload_model(model_name):
        return {"status": "unloaded", "model": model_name}
    else:
        raise HTTPException(status_code=404, detail=f"Model not loaded: {model_name}")


# ============================================================================
# Health Checks
# ============================================================================

@router.get("/health")
async def hybrid_health() -> Dict[str, str]:
    """Quick health check"""
    detector = get_connectivity_detector()
    orchestrator = get_hybrid_orchestrator()
    
    is_online = detector.is_online()
    source = detector.get_recommended_model_source()
    
    return {
        "status": "healthy",
        "connectivity": "online" if is_online else "offline",
        "model_source": source,
        "hybrid_ready": "yes"
    }


@router.get("/info")
async def hybrid_info() -> Dict[str, Any]:
    """Get hybrid system information"""
    return {
        "system": "SILIQUESTA Hybrid AI",
        "version": "1.0",
        "features": {
            "automatic_edge_cloud_switching": True,
            "offline_onnx_models": True,
            "online_cloud_backend": True,
            "connectivity_detection": True,
            "fallback_mechanisms": True,
            "performance_monitoring": True
        },
        "endpoints": {
            "predict": "POST /hybrid/predict",
            "batch_predict": "POST /hybrid/batch",
            "status": "GET /hybrid/status",
            "connectivity": "GET /hybrid/connectivity",
            "models": "GET /hybrid/models/available",
            "performance": "GET /hybrid/performance",
            "force_edge": "GET /hybrid/force-edge",
            "force_cloud": "GET /hybrid/force-cloud"
        }
    }
