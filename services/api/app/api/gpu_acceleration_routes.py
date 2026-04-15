"""
GPU Acceleration Integration

Integrates GPU acceleration into existing ML services.

Provides:
- GPU-accelerated training endpoints
- Distributed optimization endpoints
- Fallback mechanisms
"""

import logging
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
import asyncio
from pathlib import Path

from app.gpu_acceleration import (
    initialize_gpu_acceleration, 
    get_gpu_accelerator,
    initialize_gpu_pool,
    get_gpu_pool,
    print_gpu_status
)
from app.digital_twin_gpu import GPUDigitalTwinTrainer, TrainingConfig, create_gpu_trainer
from app.distributed_optimizer import create_distributed_optimizer, create_gpu_distributed_optimizer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/gpu", tags=["GPU Acceleration"])


class GPUStatusResponse(BaseModel):
    """GPU status response."""
    device_type: str
    device_name: str
    total_memory_gb: float
    available_memory_gb: float
    utilization_percent: float
    is_cuda_available: bool
    compute_capability: Optional[str] = None
    cuda_version: Optional[str] = None


class GPUTrainingConfig(BaseModel):
    """Configuration for GPU training."""
    batch_size: int = 64
    learning_rate: float = 0.001
    epochs: int = 100
    validation_split: float = 0.2
    early_stopping_patience: int = 10
    optimizer: str = 'adam'
    mixed_precision: bool = True


class DistributedOptimizationConfig(BaseModel):
    """Configuration for distributed optimization."""
    num_workers: int = 4
    gpu_per_worker: float = 0.25
    population_size: int = 100
    generations: int = 50


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    gpu_available: bool
    device_info: Dict


# ============================================================================
# GPU Status Endpoints
# ============================================================================


@router.get("/status", response_model=GPUStatusResponse)
async def get_gpu_status():
    """Get GPU device status and memory information."""
    try:
        accelerator = get_gpu_accelerator()
        info = accelerator.get_device_info()
        stats = accelerator.get_memory_stats()
        
        return GPUStatusResponse(
            device_type=info.device_type,
            device_name=info.device_name,
            total_memory_gb=info.memory_total_gb,
            available_memory_gb=info.memory_available_gb,
            utilization_percent=stats.get('utilization_percent', 0),
            is_cuda_available=accelerator.is_cuda_available(),
            compute_capability=str(info.compute_capability) if info.compute_capability else None,
            cuda_version=info.cuda_version
        )
    except Exception as e:
        logger.error(f"Error getting GPU status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def gpu_health():
    """Health check for GPU acceleration."""
    try:
        accelerator = get_gpu_accelerator()
        return HealthResponse(
            status="ok",
            gpu_available=accelerator.is_cuda_available(),
            device_info={
                "device": accelerator.get_device_info().device_type,
                "name": accelerator.get_device_info().device_name,
                "memory_gb": accelerator.get_device_info().memory_total_gb
            }
        )
    except Exception as e:
        return HealthResponse(
            status="error",
            gpu_available=False,
            device_info={"error": str(e)}
        )


@router.post("/initialize")
async def initialize_gpu(use_gpu: bool = True, gpu_id: int = 0):
    """Initialize GPU acceleration."""
    try:
        accelerator = initialize_gpu_acceleration(use_gpu=use_gpu, gpu_id=gpu_id)
        print_gpu_status()
        return {
            "status": "initialized",
            "device": accelerator.get_device_info().device_type,
            "message": f"GPU acceleration initialized on {accelerator.get_device_info().device_name}"
        }
    except Exception as e:
        logger.error(f"Error initializing GPU: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pool/initialize")
async def initialize_gpu_pool_endpoint(num_gpus: int = 1):
    """Initialize GPU pool for multi-GPU processing."""
    try:
        pool = initialize_gpu_pool(use_gpu=True)
        status = pool.get_status()
        return {
            "status": "initialized",
            "num_devices": len(pool),
            "devices": status
        }
    except Exception as e:
        logger.error(f"Error initializing GPU pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memory")
async def get_memory_stats():
    """Get detailed memory statistics."""
    try:
        accelerator = get_gpu_accelerator()
        stats = accelerator.get_memory_stats()
        return {
            "device": accelerator.get_device_info().device_type,
            "stats": stats,
            "timestamp": __import__('datetime').datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear-cache")
async def clear_gpu_cache():
    """Clear GPU memory cache."""
    try:
        accelerator = get_gpu_accelerator()
        accelerator.clear_cache()
        return {
            "status": "success",
            "message": "GPU cache cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing GPU cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GPU Training Endpoints
# ============================================================================


@router.post("/training/start")
async def start_gpu_training(config: GPUTrainingConfig = None, background_tasks: BackgroundTasks = None):
    """Start GPU-accelerated training (example endpoint)."""
    try:
        if config is None:
            config = GPUTrainingConfig()
        
        # Create trainer with config
        training_config = TrainingConfig(
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            epochs=config.epochs,
            validation_split=config.validation_split,
            early_stopping_patience=config.early_stopping_patience,
            optimizer=config.optimizer,
            mixed_precision=config.mixed_precision
        )
        
        trainer = create_gpu_trainer(training_config)
        
        return {
            "status": "ready",
            "device": trainer.device.type,
            "config": config.dict(),
            "message": "GPU trainer initialized and ready for training"
        }
    except Exception as e:
        logger.error(f"Error starting GPU training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Distributed Optimization Endpoints
# ============================================================================


@router.post("/optimization/distributed/start")
async def start_distributed_optimization(config: DistributedOptimizationConfig = None):
    """Start distributed optimization with Ray."""
    try:
        if config is None:
            config = DistributedOptimizationConfig()
        
        # Create distributed optimizer
        optimizer = create_gpu_distributed_optimizer(
            use_gpu=(config.gpu_per_worker > 0),
            num_workers=config.num_workers
        )
        
        status = optimizer.get_status()
        
        return {
            "status": "initialized",
            "config": config.dict(),
            "ray_status": status,
            "message": f"Distributed optimizer initialized with {config.num_workers} workers"
        }
    except Exception as e:
        logger.error(f"Error starting distributed optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/optimization/distributed/status")
async def get_distributed_optimization_status():
    """Get status of distributed optimization system."""
    try:
        import ray
        
        if not ray.is_initialized():
            return {
                "status": "not_initialized",
                "message": "Ray cluster not initialized"
            }
        
        return {
            "status": "initialized",
            "cluster_resources": dict(ray.available_resources()),
            "nodes": len(ray.nodes()),
            "message": "Ray cluster is running"
        }
    except Exception as e:
        logger.error(f"Error getting distributed optimization status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimization/distributed/shutdown")
async def shutdown_distributed_optimization():
    """Shutdown Ray cluster."""
    try:
        import ray
        
        if ray.is_initialized():
            ray.shutdown()
            return {
                "status": "success",
                "message": "Ray cluster shut down"
            }
        else:
            return {
                "status": "info",
                "message": "Ray cluster was not initialized"
            }
    except Exception as e:
        logger.error(f"Error shutting down Ray cluster: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# System Information
# ============================================================================


@router.get("/system-info")
async def get_system_info():
    """Get system information including GPU details."""
    try:
        import psutil
        import torch
        
        accelerator = get_gpu_accelerator()
        pool = get_gpu_pool()
        
        return {
            "system": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / 1e9,
                "memory_available_gb": psutil.virtual_memory().available / 1e9,
                "memory_percent": psutil.virtual_memory().percent
            },
            "pytorch": {
                "version": torch.__version__,
                "cuda_available": torch.cuda.is_available(),
                "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
                "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
            },
            "gpu": {
                "accelerator": str(accelerator),
                "pool_size": len(pool),
                "devices": pool.get_status()
            }
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Initialization
# ============================================================================


async def on_startup():
    """Initialize GPU acceleration on startup."""
    try:
        logger.info("Initializing GPU acceleration...")
        accelerator = initialize_gpu_acceleration(use_gpu=True)
        logger.info(f"GPU acceleration initialized: {accelerator}")
        print_gpu_status()
    except Exception as e:
        logger.warning(f"Could not initialize GPU acceleration: {e}")
        logger.info("Continuing with CPU-only mode")
