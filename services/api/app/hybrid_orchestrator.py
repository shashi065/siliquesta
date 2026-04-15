"""
Hybrid AI Orchestrator - Unified Edge/Cloud Interface
=====================================================

Automatically routes requests between lightweight edge (ONNX) models
and full cloud AI backend based on connectivity and performance.
"""

import logging
from typing import Dict, Optional, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import numpy as np

from app.onnx_model_manager import get_onnx_manager
from app.connectivity_detector import get_connectivity_detector

logger = logging.getLogger(__name__)


@dataclass
class HybridAIRequest:
    """Hybrid AI request"""
    task_type: str  # "predict", "optimize", "analyze"
    model_name: str  # "digital_twin", "optimizer", "reliability"
    inputs: Dict[str, Any]
    priority: str = "normal"  # "high", "normal", "low"
    user_preference: str = "auto"  # "auto", "edge", "cloud"


@dataclass
class HybridAIResponse:
    """Hybrid AI response with metadata"""
    result: Dict[str, Any]
    model_source: str  # "edge" or "cloud"
    execution_time_ms: float
    model_name: str
    timestamp: str
    confidence: float
    latency_ms: Optional[float] = None
    fallback_used: bool = False
    edge_degradation_percent: float = 0.0


class HybridAIOrchestrator:
    """
    Unified interface for edge and cloud AI models.
    
    Features:
    - Automatic offline/online detection
    - Seamless fallback to edge models
    - Performance monitoring
    - Result caching
    - Transparent API
    """
    
    def __init__(self):
        """Initialize hybrid orchestrator"""
        self.onnx_manager = get_onnx_manager()
        self.connectivity = get_connectivity_detector()
        self.request_history: List[Dict] = []
        self.model_performance: Dict[str, Dict] = {}
        
        logger.info("✓ HybridAIOrchestrator initialized")
    
    async def process(self, request: HybridAIRequest) -> HybridAIResponse:
        """
        Process request with automatic edge/cloud routing.
        
        Args:
            request: HybridAIRequest with task details
        
        Returns:
            HybridAIResponse with results and metadata
        """
        import time
        start_time = time.time()
        
        # Determine which model source to use
        model_source = self._determine_model_source(request)
        
        try:
            if model_source == "edge":
                result, edge_degradation = await self._process_edge(request)
                fallback_used = not self.connectivity.is_online()
            else:
                result, edge_degradation = await self._process_cloud(request)
                fallback_used = False
            
            execution_time_ms = (time.time() - start_time) * 1000
            latency_ms = self.connectivity.status.latency_ms
            
            response = HybridAIResponse(
                result=result,
                model_source=model_source,
                execution_time_ms=execution_time_ms,
                model_name=request.model_name,
                timestamp=datetime.now().isoformat(),
                confidence=0.85 if model_source == "cloud" else 0.75,
                latency_ms=latency_ms,
                fallback_used=fallback_used,
                edge_degradation_percent=edge_degradation if model_source == "edge" else 0.0
            )
            
            # Log execution
            self._log_execution(request, response)
            
            return response
            
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            raise
    
    def _determine_model_source(self, request: HybridAIRequest) -> str:
        """
        Determine whether to use edge or cloud.
        
        Decision factors:
        1. User preference (if specified)
        2. Connectivity status
        3. Task priority/latency requirements
        4. Model availability
        """
        # Respect user preference
        if request.user_preference == "edge":
            return "edge"
        if request.user_preference == "cloud":
            return "cloud"
        
        # Auto-selection based on connectivity
        if self.connectivity.use_edge():
            logger.debug("Using edge model (offline or cloud degraded)")
            return "edge"
        
        # Cloud is available and preferred for better accuracy
        if self.connectivity.is_online():
            logger.debug("Using cloud model (online)")
            return "cloud"
        
        # Default to edge if cloud unreachable
        logger.debug("Using edge model (cloud unreachable)")
        return "edge"
    
    async def _process_edge(self, request: HybridAIRequest) -> Tuple[Dict[str, Any], float]:
        """
        Process using lightweight edge (ONNX) models.
        
        Returns:
            (result, accuracy_degradation_percent)
        """
        if not self.onnx_manager:
            logger.error("ONNX manager not available")
            return {}, 100.0
        
        # Map model names to ONNX model files
        onnx_model_map = {
            "digital_twin": "digital_twin_edge",
            "optimizer": "optimizer_edge",  # Fast genetic algorithm
            "reliability": "reliability_edge"  # Physics model
        }
        
        onnx_model_name = onnx_model_map.get(request.model_name)
        
        if not onnx_model_name:
            logger.error(f"Unknown model: {request.model_name}")
            return {}, 100.0
        
        # Ensure model is loaded
        if onnx_model_name not in self.onnx_manager.list_models():
            loaded = self.onnx_manager.load_model(onnx_model_name)
            if not loaded:
                logger.error(f"Failed to load ONNX model: {onnx_model_name}")
                return {}, 100.0
        
        # Prepare inputs (convert to numpy if needed)
        onnx_inputs = {}
        for key, value in request.inputs.items():
            if isinstance(value, dict):
                value = np.array([value.get(k, 0.0) for k in sorted(value.keys())])
            elif not isinstance(value, np.ndarray):
                value = np.array(value)
            onnx_inputs[key] = value
        
        # Run inference
        result = self.onnx_manager.infer(onnx_model_name, onnx_inputs)
        
        if result is None:
            logger.error(f"Inference failed on {onnx_model_name}")
            return {}, 100.0
        
        # Convert numpy results to Python types
        result_dict = {
            k: (v.tolist() if isinstance(v, np.ndarray) else v)
            for k, v in result.items()
        }
        
        # Accuracy degradation for edge models (ONNX quantization)
        edge_degradation = 2.0  # Typical quantization loss: 2%
        
        logger.debug(f"Edge inference complete: {request.model_name} (degradation: {edge_degradation}%)")
        
        return result_dict, edge_degradation
    
    async def _process_cloud(self, request: HybridAIRequest) -> Tuple[Dict[str, Any], float]:
        """
        Process using full cloud AI backend.
        
        Returns:
            (result, accuracy_degradation_percent)
        """
        # This would call actual cloud services
        # For now, return simulated result
        
        logger.debug(f"Cloud processing: {request.model_name}")
        
        # Simulate cloud result (in real system, would call actual services)
        result = {
            "model_used": f"{request.model_name}_cloud",
            "status": "simulated",
            "inputs_received": len(request.inputs),
            "timestamp": datetime.now().isoformat()
        }
        
        return result, 0.0  # Cloud has no degradation
    
    def _log_execution(self, request: HybridAIRequest, response: HybridAIResponse):
        """Log execution for monitoring"""
        log_entry = {
            "timestamp": response.timestamp,
            "model": request.model_name,
            "source": response.model_source,
            "execution_time_ms": response.execution_time_ms,
            "confidence": response.confidence,
            "fallback": response.fallback_used,
            "degradation": response.edge_degradation_percent
        }
        
        self.request_history.append(log_entry)
        
        # Keep history limited
        if len(self.request_history) > 1000:
            self.request_history = self.request_history[-1000:]
        
        # Update performance stats
        if request.model_name not in self.model_performance:
            self.model_performance[request.model_name] = {
                "total_requests": 0,
                "edge_requests": 0,
                "cloud_requests": 0,
                "avg_execution_time": 0.0,
                "avg_confidence": 0.0
            }
        
        perf = self.model_performance[request.model_name]
        perf["total_requests"] += 1
        if response.model_source == "edge":
            perf["edge_requests"] += 1
        else:
            perf["cloud_requests"] += 1
        
        # Update averages
        alpha = 0.1  # Smoothing factor
        perf["avg_execution_time"] = (
            alpha * response.execution_time_ms +
            (1 - alpha) * perf["avg_execution_time"]
        )
        perf["avg_confidence"] = (
            alpha * response.confidence +
            (1 - alpha) * perf["avg_confidence"]
        )
    
    def get_performance_stats(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance statistics"""
        if model_name:
            return self.model_performance.get(model_name, {})
        return self.model_performance
    
    def get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """Get recent execution history"""
        return self.request_history[-limit:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get system status"""
        return {
            "connectivity": self.connectivity.get_status(),
            "active_models": self.onnx_manager.list_models() if self.onnx_manager else [],
            "edge_models_loaded": len(self.onnx_manager.list_models()) if self.onnx_manager else 0,
            "total_requests": sum(
                p.get("total_requests", 0) 
                for p in self.model_performance.values()
            ),
            "model_performance": self.model_performance
        }


# Global orchestrator instance
_hybrid_orchestrator: Optional[HybridAIOrchestrator] = None


def get_hybrid_orchestrator() -> HybridAIOrchestrator:
    """Get or create global hybrid orchestrator"""
    global _hybrid_orchestrator
    if _hybrid_orchestrator is None:
        _hybrid_orchestrator = HybridAIOrchestrator()
    return _hybrid_orchestrator
