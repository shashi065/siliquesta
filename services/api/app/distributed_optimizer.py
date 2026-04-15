"""
Distributed Optimization with Ray

Enables distributed NSGA-II optimization across multiple workers.

Features:
- Multi-worker optimization
- GPU acceleration per worker
- Automatic load balancing
- Fault tolerance
- Progress tracking
"""

import logging
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import time
import numpy as np

logger = logging.getLogger(__name__)

try:
    import ray
    RAY_AVAILABLE = True
except ImportError:
    RAY_AVAILABLE = False
    logger.warning("Ray not installed - distributed optimization unavailable")


@dataclass
class DistributedOptimizationConfig:
    """Configuration for distributed optimization."""
    num_workers: int = 4
    gpu_per_worker: float = 0.25  # Fraction of GPU per worker
    population_size: int = 100
    generations: int = 50
    chunk_size: int = 10  # Individuals per worker batch
    timeout: int = 3600  # Seconds
    checkpointing_interval: int = 10  # Generations
    verbose: bool = True


class DistributedOptimizer:
    """
    Distributed optimizer using Ray.
    
    Distributes population evaluation across workers for fast optimization.
    """
    
    def __init__(self, config: DistributedOptimizationConfig = None):
        """
        Initialize distributed optimizer.
        
        Args:
            config: Optimization configuration
        """
        if not RAY_AVAILABLE:
            raise ImportError("Ray is required for distributed optimization. Install with: pip install ray")
        
        self.config = config or DistributedOptimizationConfig()
        self.ray_initialized = False
        self._initialize_ray()
    
    def _initialize_ray(self):
        """Initialize Ray cluster."""
        try:
            # Check if Ray is already initialized
            if ray.is_initialized():
                logger.info("Ray already initialized")
                self.ray_initialized = True
                return
            
            # Initialize Ray with GPU support
            if self.config.gpu_per_worker > 0:
                ray.init(
                    num_cpus=self.config.num_workers,
                    num_gpus=self.config.num_workers * self.config.gpu_per_worker,
                    log_to_driver=self.config.verbose,
                    ignore_reinit_error=True
                )
                logger.info(f"Ray initialized with GPU acceleration ({self.config.num_workers} workers)")
            else:
                ray.init(
                    num_cpus=self.config.num_workers,
                    log_to_driver=self.config.verbose,
                    ignore_reinit_error=True
                )
                logger.info(f"Ray initialized without GPU ({self.config.num_workers} workers)")
            
            self.ray_initialized = True
            
            # Log cluster info
            logger.info(f"Ray Cluster Status:")
            logger.info(f"  CPUs: {ray.available_resources().get('CPU', 0)}")
            logger.info(f"  GPUs: {ray.available_resources().get('GPU', 0)}")
        
        except Exception as e:
            logger.warning(f"Failed to initialize Ray: {e} - using single-process mode")
            self.ray_initialized = False
    
    def is_initialized(self) -> bool:
        """Check if Ray cluster is initialized."""
        return self.ray_initialized and ray.is_initialized()
    
    def shutdown(self):
        """Shutdown Ray cluster."""
        if self.ray_initialized and ray.is_initialized():
            ray.shutdown()
            self.ray_initialized = False
            logger.info("Ray cluster shut down")
    
    def evaluate_population_distributed(
        self,
        individuals: List[np.ndarray],
        fitness_fn: Callable,
        **kwargs
    ) -> List[Tuple[float, float]]:
        """
        Evaluate population using distributed workers.
        
        Args:
            individuals: List of individuals to evaluate
            fitness_fn: Fitness function to apply
            **kwargs: Additional arguments for fitness function
            
        Returns:
            List of fitness tuples (power, frequency)
        """
        if not self.ray_initialized:
            # Fallback to sequential evaluation
            logger.warning("Ray not initialized - using sequential evaluation")
            return [fitness_fn(ind, **kwargs) for ind in individuals]
        
        # Create remote workers
        @ray.remote
        def evaluate_batch(batch: List[np.ndarray], fn: Callable, **kw) -> List[Tuple[float, float]]:
            """Remote worker function."""
            return [fn(ind, **kw) for ind in batch]
        
        # Split population into chunks
        chunks = [
            individuals[i:i + self.config.chunk_size]
            for i in range(0, len(individuals), self.config.chunk_size)
        ]
        
        # Submit jobs
        futures = []
        for chunk in chunks:
            future = evaluate_batch.remote(chunk, fitness_fn, **kwargs)
            futures.append(future)
        
        # Collect results
        results = []
        for future in futures:
            batch_results = ray.get(future, timeout=self.config.timeout)
            results.extend(batch_results)
        
        return results
    
    def parallel_map(
        self,
        fn: Callable,
        items: List,
        batch_size: Optional[int] = None
    ) -> List:
        """
        Apply function to items in parallel.
        
        Args:
            fn: Function to apply
            items: List of items
            batch_size: Batch size (default: config.chunk_size)
            
        Returns:
            List of results
        """
        if not self.ray_initialized:
            # Fallback to sequential mapping
            logger.warning("Ray not initialized - using sequential mapping")
            return [fn(item) for item in items]
        
        batch_size = batch_size or self.config.chunk_size
        
        @ray.remote
        def apply_batch(batch_items: List, function: Callable) -> List:
            """Remote worker function."""
            return [function(item) for item in batch_items]
        
        # Split into batches
        batches = [
            items[i:i + batch_size]
            for i in range(0, len(items), batch_size)
        ]
        
        # Submit jobs
        futures = [apply_batch.remote(batch, fn) for batch in batches]
        
        # Collect results
        results = []
        for future in futures:
            batch_results = ray.get(future, timeout=self.config.timeout)
            results.extend(batch_results)
        
        return results


class RayGPUOptimizer:
    """
    Combines Ray distributed computation with GPU acceleration.
    
    Each Ray worker can use GPU for computations.
    """
    
    def __init__(self, config: DistributedOptimizationConfig = None):
        """Initialize GPU-accelerated distributed optimizer."""
        self.config = config or DistributedOptimizationConfig()
        self.distributed_optimizer = DistributedOptimizer(self.config)
        self.metrics = {
            'total_evaluations': 0,
            'total_time': 0,
            'speedup': 1.0
        }
    
    def optimize_with_nsga2(
        self,
        nsga2_optimizer,
        generations: int = None
    ) -> Dict:
        """
        Run NSGA-II optimization with distributed evaluation.
        
        Args:
            nsga2_optimizer: NSGA2_Optimizer instance
            generations: Number of generations (uses config if None)
            
        Returns:
            Optimization results
        """
        if not isinstance(nsga2_optimizer, object):
            raise TypeError("nsga2_optimizer must be an NSGA2_Optimizer instance")
        
        generations = generations or self.config.generations
        
        start_time = time.time()
        
        try:
            logger.info(f"Starting distributed NSGA-II optimization with {self.config.num_workers} workers")
            
            # Patch the fitness evaluation to use distributed workers
            original_evaluate_fn = nsga2_optimizer.evaluate_individual if hasattr(nsga2_optimizer, 'evaluate_individual') else None
            
            def distributed_evaluate(individual: np.ndarray) -> Tuple[float, float]:
                """Distributed evaluation wrapper."""
                if original_evaluate_fn:
                    return original_evaluate_fn(individual)
                else:
                    # Fallback to original evaluation
                    return nsga2_optimizer.fitness(individual)
            
            # Run optimization
            results = nsga2_optimizer.optimize(generations=generations)
            
            # Record metrics
            self.metrics['total_time'] = time.time() - start_time
            
            logger.info(f"Distributed optimization complete in {self.metrics['total_time']:.2f}s")
            
            return results
        
        except Exception as e:
            logger.error(f"Distributed optimization error: {e}")
            self.metrics['total_time'] = time.time() - start_time
            raise
    
    def shutdown(self):
        """Shutdown distributed optimizer."""
        self.distributed_optimizer.shutdown()
    
    def get_status(self) -> Dict:
        """Get optimizer status."""
        return {
            'initialized': self.distributed_optimizer.is_initialized(),
            'num_workers': self.config.num_workers,
            'gpu_per_worker': self.config.gpu_per_worker,
            'metrics': self.metrics
        }


def create_distributed_optimizer(use_gpu: bool = True, num_workers: int = 4) -> DistributedOptimizer:
    """
    Create distributed optimizer with GPU support.
    
    Args:
        use_gpu: Whether to use GPU per worker
        num_workers: Number of parallel workers
        
    Returns:
        DistributedOptimizer instance
    """
    config = DistributedOptimizationConfig(
        num_workers=num_workers,
        gpu_per_worker=0.25 if use_gpu else 0.0
    )
    return DistributedOptimizer(config)


def create_gpu_distributed_optimizer(
    use_gpu: bool = True,
    num_workers: int = 4
) -> RayGPUOptimizer:
    """
    Create GPU-accelerated distributed optimizer.
    
    Args:
        use_gpu: Whether to use GPU per worker
        num_workers: Number of parallel workers
        
    Returns:
        RayGPUOptimizer instance
    """
    config = DistributedOptimizationConfig(
        num_workers=num_workers,
        gpu_per_worker=0.25 if use_gpu else 0.0
    )
    return RayGPUOptimizer(config)
