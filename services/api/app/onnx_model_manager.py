"""
ONNX Model Manager - Lightweight Edge Inference
===============================================

Manages ONNX models for fast, lightweight inference on edge devices.
Models run entirely offline without cloud dependencies.
"""

import os
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import onnx
    import onnxruntime as ort
    ONNX_AVAILABLE = True
except ImportError:
    ONNX_AVAILABLE = False
    logger.warning("ONNX not available - install 'onnxruntime' for edge inference")


@dataclass
class ONNXModelMetadata:
    """Metadata for ONNX model"""
    name: str
    version: str
    input_names: List[str]
    output_names: List[str]
    input_shapes: Dict[str, Tuple]
    input_types: Dict[str, str]
    model_size_mb: float
    quantized: bool
    accuracy_loss_percent: float = 0.0


class ONNXModelManager:
    """
    Manages ONNX models for edge inference.
    
    Features:
    - Load pre-converted ONNX models
    - Quantized models for faster inference
    - Batch inference support
    - Model caching
    """
    
    def __init__(self, models_dir: str = "ai-engine/models/onnx"):
        """Initialize ONNX model manager"""
        self.models_dir = Path(models_dir)
        self.models: Dict[str, ort.InferenceSession] = {}
        self.metadata: Dict[str, ONNXModelMetadata] = {}
        self.cache_enabled = True
        
        if not ONNX_AVAILABLE:
            logger.error("ONNX Runtime not available")
            return
        
        # Create models directory if doesn't exist
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"✓ ONNX Model Manager initialized (models_dir: {self.models_dir})")
    
    def load_model(self, model_name: str, model_path: Optional[str] = None) -> bool:
        """
        Load ONNX model.
        
        Args:
            model_name: Name identifier for model
            model_path: Path to .onnx file (auto-discovered if None)
        
        Returns:
            True if loaded successfully
        """
        if not ONNX_AVAILABLE:
            logger.error("ONNX Runtime not available")
            return False
        
        try:
            # Auto-discover if path not provided
            if model_path is None:
                model_path = self.models_dir / f"{model_name}.onnx"
            
            model_path = Path(model_path)
            
            if not model_path.exists():
                logger.error(f"Model file not found: {model_path}")
                return False
            
            # Load ONNX model with optimized settings
            sess_options = ort.SessionOptions()
            sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            sess_options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            
            # Use CPU for edge devices (no GPU dependency)
            session = ort.InferenceSession(
                str(model_path),
                sess_options=sess_options,
                providers=['CPUExecutionProvider']
            )
            
            # Extract metadata
            model_proto = onnx.load(str(model_path))
            
            input_names = [inp.name for inp in model_proto.graph.input]
            output_names = [out.name for out in model_proto.graph.output]
            
            input_shapes = {}
            input_types = {}
            for inp in model_proto.graph.input:
                dims = [d.dim_value if d.dim_value > 0 else None for d in inp.type.tensor_type.shape.dim]
                input_shapes[inp.name] = tuple(dims)
                input_types[inp.name] = str(inp.type.tensor_type.data_type)
            
            model_size_mb = model_path.stat().st_size / (1024 * 1024)
            
            # Determine if quantized (int8 or uint8 in model name)
            quantized = 'quant' in model_name.lower() or 'int8' in model_name.lower()
            
            metadata = ONNXModelMetadata(
                name=model_name,
                version="1.0",
                input_names=input_names,
                output_names=output_names,
                input_shapes=input_shapes,
                input_types=input_types,
                model_size_mb=model_size_mb,
                quantized=quantized,
                accuracy_loss_percent=2.0 if quantized else 0.0
            )
            
            self.models[model_name] = session
            self.metadata[model_name] = metadata
            
            logger.info(f"✓ Loaded ONNX model: {model_name} ({model_size_mb:.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load ONNX model {model_name}: {e}")
            return False
    
    def infer(self, model_name: str, inputs: Dict[str, np.ndarray]) -> Optional[Dict[str, np.ndarray]]:
        """
        Run inference on model.
        
        Args:
            model_name: Model identifier
            inputs: Dictionary of input arrays
        
        Returns:
            Dictionary of output arrays, or None on error
        """
        if not ONNX_AVAILABLE or model_name not in self.models:
            logger.error(f"Model not loaded: {model_name}")
            return None
        
        try:
            session = self.models[model_name]
            
            # Run inference
            outputs = session.run(None, inputs)
            
            # Map output names to arrays
            metadata = self.metadata[model_name]
            result = {
                name: output for name, output in zip(metadata.output_names, outputs)
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Inference failed on {model_name}: {e}")
            return None
    
    def infer_batch(self, model_name: str, batch_inputs: List[Dict[str, np.ndarray]]) -> Optional[List[Dict[str, np.ndarray]]]:
        """
        Run batch inference.
        
        Args:
            model_name: Model identifier
            batch_inputs: List of input dictionaries
        
        Returns:
            List of output dictionaries
        """
        results = []
        for inputs in batch_inputs:
            result = self.infer(model_name, inputs)
            if result is not None:
                results.append(result)
        
        return results if results else None
    
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model metadata"""
        if model_name not in self.metadata:
            return None
        
        meta = self.metadata[model_name]
        return {
            "name": meta.name,
            "version": meta.version,
            "input_names": meta.input_names,
            "output_names": meta.output_names,
            "input_shapes": meta.input_shapes,
            "model_size_mb": meta.model_size_mb,
            "quantized": meta.quantized,
            "accuracy_loss_percent": meta.accuracy_loss_percent
        }
    
    def list_models(self) -> List[str]:
        """List loaded models"""
        return list(self.models.keys())
    
    def unload_model(self, model_name: str) -> bool:
        """Unload model to free memory"""
        if model_name in self.models:
            del self.models[model_name]
            del self.metadata[model_name]
            logger.info(f"✓ Unloaded model: {model_name}")
            return True
        return False


# Global manager instance
_onnx_manager: Optional[ONNXModelManager] = None


def get_onnx_manager() -> Optional[ONNXModelManager]:
    """Get or create global ONNX manager"""
    global _onnx_manager
    if _onnx_manager is None and ONNX_AVAILABLE:
        _onnx_manager = ONNXModelManager()
    return _onnx_manager


def create_quantized_onnx_models():
    """
    Create placeholder ONNX models for demonstration.
    In production, these would be pre-converted from trained models.
    """
    if not ONNX_AVAILABLE:
        logger.warning("ONNX not available - skipping model creation")
        return
    
    models_dir = Path("ai-engine/models/onnx")
    models_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Create simple CMOS prediction model
        # This is a minimal example - production would use actual converted models
        
        # Digital Twin lightweight model (for power/freq/delay prediction)
        DT_MODEL_PATH = models_dir / "digital_twin_edge.onnx"
        if not DT_MODEL_PATH.exists():
            # Create a minimal model for testing
            import onnx
            from onnx import helper, TensorProto
            
            X = helper.make_tensor_value_info('X', TensorProto.FLOAT, [None, 4])
            Y = helper.make_tensor_value_info('Y', TensorProto.FLOAT, [None, 3])
            
            # Simple linear transformation (in production: actual neural network)
            const_tensor = helper.make_tensor(
                name='weights',
                data_type=TensorProto.FLOAT,
                dims=[4, 3],
                vals=np.random.randn(4, 3).flatten().tolist()
            )
            
            const_init = helper.make_node(
                'Constant',
                inputs=[],
                outputs=['W'],
                value=const_tensor
            )
            
            matmul_node = helper.make_node(
                'MatMul',
                inputs=['X', 'W'],
                outputs=['Y']
            )
            
            graph_def = helper.make_graph(
                [const_init, matmul_node],
                'DigitalTwinEdge',
                [X], [Y],
                [const_tensor]
            )
            
            model_def = helper.make_model(
                graph_def,
                producer_name='siliquesta',
                opset_imports=[helper.make_opsetid("", 12)]
            )
            
            onnx.save(model_def, str(DT_MODEL_PATH))
            logger.info(f"✓ Created ONNX model: {DT_MODEL_PATH}")
        
    except Exception as e:
        logger.warning(f"Could not create ONNX models: {e}")
