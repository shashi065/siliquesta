"""
GPU Acceleration Infrastructure

Provides GPU/CUDA support with automatic CPU fallback.

Features:
- Automatic CUDA device detection
- Memory management and optimization
- CPU fallback if no GPU available
- Device status monitoring
- Multi-GPU support
"""

import torch
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import psutil

logger = logging.getLogger(__name__)


@dataclass
class DeviceInfo:
    """Information about compute device."""
    device_type: str  # 'cuda', 'cpu'
    device_id: int = 0
    device_name: str = ''
    memory_total_gb: float = 0
    memory_available_gb: float = 0
    compute_capability: Optional[Tuple[int, int]] = None
    cuda_version: Optional[str] = None
    is_available: bool = True
    

class GPUAccelerator:
    """
    Manages GPU acceleration with CPU fallback.
    
    Features:
    - Automatic device selection
    - Memory monitoring
    - CPU fallback
    - Multi-GPU support
    - Performance profiling
    """
    
    def __init__(self, use_gpu: bool = True, gpu_id: int = 0, memory_fraction: float = 0.8):
        """
        Initialize GPU accelerator.
        
        Args:
            use_gpu: Whether to use GPU if available
            gpu_id: GPU device ID to use
            memory_fraction: Maximum fraction of GPU memory to use (0.0-1.0)
        """
        self.use_gpu = use_gpu
        self.gpu_id = gpu_id
        self.memory_fraction = memory_fraction
        self.device = self._initialize_device()
        self.device_info = self._get_device_info()
        
        # Performance metrics
        self.total_gpu_allocations = 0
        self.total_data_transfers = 0
        self.total_compute_time = 0
        
    def _initialize_device(self) -> torch.device:
        """Initialize and select compute device."""
        if not self.use_gpu:
            logger.info("GPU disabled by user - using CPU")
            return torch.device('cpu')
        
        # Check CUDA availability
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - falling back to CPU")
            return torch.device('cpu')
        
        # Check device count
        device_count = torch.cuda.device_count()
        if self.gpu_id >= device_count:
            logger.warning(f"GPU {self.gpu_id} not available (only {device_count} GPUs found) - using CPU")
            return torch.device('cpu')
        
        # Select device
        device = torch.device(f'cuda:{self.gpu_id}')
        
        # Set memory management
        try:
            torch.cuda.set_per_process_memory_fraction(self.memory_fraction, device)
            logger.info(f"CUDA device {self.gpu_id} selected with {self.memory_fraction*100:.0f}% memory limit")
        except Exception as e:
            logger.warning(f"Could not set memory fraction: {e}")
        
        return device
    
    def _get_device_info(self) -> DeviceInfo:
        """Get detailed device information."""
        if self.device.type == 'cuda':
            device_id = self.device.index or 0
            device_name = torch.cuda.get_device_name(device_id)
            properties = torch.cuda.get_device_properties(device_id)
            
            # Get memory info
            allocated = torch.cuda.memory_allocated(device_id) / 1e9
            reserved = torch.cuda.memory_reserved(device_id) / 1e9
            total = properties.total_memory / 1e9
            available = total - reserved
            
            return DeviceInfo(
                device_type='cuda',
                device_id=device_id,
                device_name=device_name,
                memory_total_gb=total,
                memory_available_gb=available,
                compute_capability=(properties.major, properties.minor),
                cuda_version=torch.version.cuda,
                is_available=True
            )
        else:
            # CPU info
            available_memory = psutil.virtual_memory().available / 1e9
            total_memory = psutil.virtual_memory().total / 1e9
            
            return DeviceInfo(
                device_type='cpu',
                device_id=0,
                device_name=f'CPU ({psutil.cpu_count()} cores)',
                memory_total_gb=total_memory,
                memory_available_gb=available_memory,
                is_available=True
            )
    
    def get_device(self) -> torch.device:
        """Get current device."""
        return self.device
    
    def get_device_info(self) -> DeviceInfo:
        """Get device information."""
        if self.device.type == 'cuda':
            # Update memory info
            device_id = self.device.index or 0
            properties = torch.cuda.get_device_properties(device_id)
            total = properties.total_memory / 1e9
            reserved = torch.cuda.memory_reserved(device_id) / 1e9
            available = total - reserved
            
            self.device_info.memory_available_gb = available
        else:
            # Update CPU memory
            self.device_info.memory_available_gb = psutil.virtual_memory().available / 1e9
        
        return self.device_info
    
    def to_device(self, tensor: torch.Tensor) -> torch.Tensor:
        """Move tensor to device with error handling."""
        try:
            self.total_data_transfers += 1
            return tensor.to(self.device)
        except RuntimeError as e:
            logger.error(f"Failed to move tensor to {self.device}: {e}")
            # Fallback to CPU
            self.device = torch.device('cpu')
            return tensor.to(self.device)
    
    def clear_cache(self):
        """Clear device cache."""
        if self.device.type == 'cuda':
            torch.cuda.empty_cache()
            logger.debug("CUDA cache cleared")
    
    def get_memory_stats(self) -> Dict[str, float]:
        """Get memory statistics."""
        if self.device.type == 'cuda':
            device_id = self.device.index or 0
            allocated = torch.cuda.memory_allocated(device_id) / 1e9
            reserved = torch.cuda.memory_reserved(device_id) / 1e9
            properties = torch.cuda.get_device_properties(device_id)
            total = properties.total_memory / 1e9
            
            return {
                'total_gb': total,
                'allocated_gb': allocated,
                'reserved_gb': reserved,
                'free_gb': total - reserved,
                'utilization_percent': (allocated / total) * 100 if total > 0 else 0
            }
        else:
            vm = psutil.virtual_memory()
            return {
                'total_gb': vm.total / 1e9,
                'used_gb': vm.used / 1e9,
                'available_gb': vm.available / 1e9,
                'utilization_percent': vm.percent
            }
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available and active."""
        return self.device.type == 'cuda' and torch.cuda.is_available()
    
    def __repr__(self) -> str:
        """String representation."""
        info = self.get_device_info()
        return (f"GPUAccelerator(device={info.device_type}, "
                f"name={info.device_name}, "
                f"memory={info.memory_available_gb:.1f}/{info.memory_total_gb:.1f} GB)")


class GPUPool:
    """
    Manages multiple GPUs for parallel processing.
    
    Distributes computations across available GPUs.
    """
    
    def __init__(self, use_gpu: bool = True):
        """Initialize GPU pool."""
        self.use_gpu = use_gpu
        self.devices = self._initialize_pool()
        self.allocation_idx = 0
    
    def _initialize_pool(self) -> List[GPUAccelerator]:
        """Initialize pool of GPUs."""
        if not self.use_gpu:
            return [GPUAccelerator(use_gpu=False)]
        
        # Detect available GPUs
        if not torch.cuda.is_available():
            logger.warning("CUDA not available - creating CPU-only pool")
            return [GPUAccelerator(use_gpu=False)]
        
        device_count = torch.cuda.device_count()
        logger.info(f"Found {device_count} GPU device(s)")
        
        # Create accelerators for each GPU
        accelerators = []
        for i in range(device_count):
            try:
                acc = GPUAccelerator(use_gpu=True, gpu_id=i)
                accelerators.append(acc)
                logger.info(f"  GPU {i}: {acc.get_device_info().device_name}")
            except Exception as e:
                logger.warning(f"Failed to initialize GPU {i}: {e}")
        
        # Fallback to CPU if no GPUs available
        if not accelerators:
            logger.warning("No GPUs successfully initialized - falling back to CPU")
            return [GPUAccelerator(use_gpu=False)]
        
        return accelerators
    
    def get_device(self, device_id: Optional[int] = None) -> torch.device:
        """Get device from pool."""
        if device_id is not None:
            if 0 <= device_id < len(self.devices):
                return self.devices[device_id].get_device()
            else:
                logger.warning(f"Device {device_id} not in pool - using device 0")
        
        return self.devices[0].get_device()
    
    def get_next_device(self) -> torch.device:
        """Get next device in round-robin fashion."""
        device = self.devices[self.allocation_idx].get_device()
        self.allocation_idx = (self.allocation_idx + 1) % len(self.devices)
        return device
    
    def get_device_info(self, device_id: int = 0) -> DeviceInfo:
        """Get device information."""
        if 0 <= device_id < len(self.devices):
            return self.devices[device_id].get_device_info()
        return self.devices[0].get_device_info()
    
    def get_status(self) -> Dict:
        """Get status of all devices in pool."""
        return {
            f"device_{i}": {
                "info": {
                    "device_type": dev.get_device_info().device_type,
                    "device_name": dev.get_device_info().device_name,
                },
                "memory": dev.get_memory_stats(),
                "is_available": dev.get_device_info().is_available
            }
            for i, dev in enumerate(self.devices)
        }
    
    def __len__(self) -> int:
        """Number of devices in pool."""
        return len(self.devices)
    
    def __repr__(self) -> str:
        """String representation."""
        return f"GPUPool(devices={len(self.devices)})"


# Global GPU accelerator instance
_global_accelerator: Optional[GPUAccelerator] = None
_global_pool: Optional[GPUPool] = None


def initialize_gpu_acceleration(use_gpu: bool = True, gpu_id: int = 0) -> GPUAccelerator:
    """
    Initialize global GPU accelerator.
    
    Args:
        use_gpu: Whether to use GPU if available
        gpu_id: GPU device ID to use
        
    Returns:
        GPUAccelerator instance
    """
    global _global_accelerator
    _global_accelerator = GPUAccelerator(use_gpu=use_gpu, gpu_id=gpu_id)
    logger.info(f"GPU acceleration initialized: {_global_accelerator}")
    return _global_accelerator


def get_gpu_accelerator() -> GPUAccelerator:
    """Get global GPU accelerator."""
    global _global_accelerator
    if _global_accelerator is None:
        _global_accelerator = initialize_gpu_acceleration()
    return _global_accelerator


def initialize_gpu_pool(use_gpu: bool = True) -> GPUPool:
    """
    Initialize global GPU pool.
    
    Args:
        use_gpu: Whether to use GPUs if available
        
    Returns:
        GPUPool instance
    """
    global _global_pool
    _global_pool = GPUPool(use_gpu=use_gpu)
    logger.info(f"GPU pool initialized: {_global_pool}")
    return _global_pool


def get_gpu_pool() -> GPUPool:
    """Get global GPU pool."""
    global _global_pool
    if _global_pool is None:
        _global_pool = initialize_gpu_pool()
    return _global_pool


def get_device() -> torch.device:
    """Get current compute device."""
    return get_gpu_accelerator().get_device()


def is_gpu_available() -> bool:
    """Check if GPU is available and active."""
    return get_gpu_accelerator().is_cuda_available()


def get_device_info() -> DeviceInfo:
    """Get information about current device."""
    return get_gpu_accelerator().get_device_info()


def get_device_stats() -> Dict:
    """Get memory and device statistics."""
    return get_gpu_accelerator().get_memory_stats()


def print_gpu_status():
    """Print GPU status information."""
    accelerator = get_gpu_accelerator()
    info = accelerator.get_device_info()
    stats = accelerator.get_memory_stats()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"GPU Status")
    logger.info(f"{'='*60}")
    logger.info(f"Device Type:        {info.device_type}")
    logger.info(f"Device Name:        {info.device_name}")
    logger.info(f"Total Memory:       {info.memory_total_gb:.2f} GB")
    logger.info(f"Available Memory:   {info.memory_available_gb:.2f} GB")
    
    if info.device_type == 'cuda':
        logger.info(f"CUDA Compute Cap:   {info.compute_capability}")
        logger.info(f"CUDA Version:       {info.cuda_version}")
        logger.info(f"Memory Allocated:   {stats['allocated_gb']:.2f} GB")
        logger.info(f"Memory Reserved:    {stats['reserved_gb']:.2f} GB")
        logger.info(f"Utilization:        {stats['utilization_percent']:.1f}%")
    else:
        logger.info(f"Memory Used:        {stats['used_gb']:.2f} GB")
        logger.info(f"Utilization:        {stats['utilization_percent']:.1f}%")
    
    logger.info(f"{'='*60}\n")
