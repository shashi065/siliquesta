"""Job worker for processing simulation and optimization jobs.

Handles job execution, result handling, parallel processing,
and error management.
"""

import asyncio
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cache import get_cache
from app.services.job_queue import JobQueue, JobStatus, get_job_queue

logger = logging.getLogger(__name__)


class JobWorker:
    """Processes jobs from queue with parallel execution and caching."""

    def __init__(
        self,
        job_queue: Optional[JobQueue] = None,
        num_workers: int = 4,
        job_handlers: Optional[dict[str, Callable]] = None,
    ):
        """Initialize job worker.
        
        Args:
            job_queue: Job queue instance
            num_workers: Number of parallel workers
            job_handlers: Dict mapping job types to handler functions
        """
        self.job_queue = job_queue or get_job_queue()
        self.cache = get_cache()
        self.num_workers = num_workers
        self.job_handlers: dict[str, Callable] = job_handlers or {}
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
        self.is_running = False

    def register_handler(self, job_type: str, handler: Callable) -> None:
        """Register handler for job type.
        
        Args:
            job_type: Type of job ('simulate', 'optimize', etc.)
            handler: Async function to handle job
        """
        self.job_handlers[job_type] = handler
        logger.info(f"📝 Registered handler for job type: {job_type}")

    async def start(self, poll_interval: float = 1.0) -> None:
        """Start worker event loop.
        
        Args:
            poll_interval: Seconds between queue polls
        """
        self.is_running = True
        logger.info(f"🚀 Starting job worker with {self.num_workers} workers...")
        
        try:
            while self.is_running:
                # Process multiple jobs in parallel
                pending_tasks = []
                
                for _ in range(self.num_workers):
                    job_data = self.job_queue.dequeue()
                    if job_data:
                        job_key, data = job_data
                        task = asyncio.create_task(self._process_job(job_key, data))
                        pending_tasks.append(task)
                
                # Wait for tasks to complete
                if pending_tasks:
                    await asyncio.gather(*pending_tasks, return_exceptions=True)
                else:
                    # No jobs available, sleep before polling again
                    await asyncio.sleep(poll_interval)
        except Exception as e:
            logger.error(f"❌ Worker error: {e}")
        finally:
            self.is_running = False
            logger.info("🛑 Job worker stopped")

    def stop(self) -> None:
        """Stop worker event loop."""
        self.is_running = False
        logger.info("⏹️  Stopping job worker...")

    async def _process_job(self, job_key: str, job_data: dict[str, Any]) -> None:
        """Process a single job.
        
        Args:
            job_key: Job identifier
            job_data: Job data
        """
        job_type = job_data.get("type", "unknown")
        user_id = job_data.get("user_id")
        params = job_data.get("params", {})
        
        logger.info(f"▶️  Processing job: {job_key} (type: {job_type})")
        
        db = next(get_db())
        
        try:
            # Check cache first
            cached_result = self.cache.get_simulation_cache(params, user_id)
            if cached_result and isinstance(cached_result, dict) and cached_result.get("status") != "warming":
                logger.info(f"🎯 Cache hit for job {job_key}")
                self.job_queue.mark_completed(job_key, cached_result, db)
                return
            
            # Get handler for job type
            handler = self.job_handlers.get(job_type)
            if not handler:
                error = f"No handler registered for job type: {job_type}"
                logger.error(f"❌ {error}")
                self.job_queue.mark_failed(job_key, error, db)
                return
            
            # Execute job (handler should be async)
            result = await handler(params, user_id=user_id)
            
            # Cache result
            self.cache.cache_simulation_result(params, result, user_id)
            
            # Mark as completed
            self.job_queue.mark_completed(job_key, result, db)
            logger.info(f"✅ Job completed: {job_key}")
        
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ Job failed: {job_key} - {error_msg}")
            self.job_queue.mark_failed(job_key, error_msg, db)
        
        finally:
            db.close()

    def process_jobs_sync(self, max_jobs: int = 10) -> dict[str, Any]:
        """Process jobs synchronously (blocking).
        
        Useful for batch processing or testing.
        
        Args:
            max_jobs: Maximum jobs to process
            
        Returns:
            Summary of processed jobs
        """
        logger.info(f"🔄 Processing up to {max_jobs} jobs synchronously...")
        
        processed = 0
        succeeded = 0
        failed = 0
        
        db = next(get_db())
        
        try:
            for _ in range(max_jobs):
                job_data = self.job_queue.dequeue()
                if not job_data:
                    break
                
                job_key, data = job_data
                
                try:
                    # Process synchronously using asyncio.run
                    asyncio.run(self._process_job(job_key, data))
                    succeeded += 1
                except Exception as e:
                    logger.error(f"❌ Sync job failed: {job_key} - {e}")
                    failed += 1
                
                processed += 1
        
        finally:
            db.close()
        
        summary = {
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "queue_stats": self.job_queue.get_queue_stats(),
            "cache_stats": self.cache.get_stats(),
        }
        
        logger.info(f"📊 Processing complete: {succeeded}/{processed} succeeded")
        return summary

    def get_job_status(self, job_key: str) -> Optional[dict[str, Any]]:
        """Get status of a job.
        
        Args:
            job_key: Job identifier
            
        Returns:
            Job data or None
        """
        return self.job_queue.get_status(job_key)

    def get_stats(self) -> dict[str, Any]:
        """Get worker statistics.
        
        Returns:
            Worker and system stats
        """
        return {
            "is_running": self.is_running,
            "num_workers": self.num_workers,
            "registered_handlers": list(self.job_handlers.keys()),
            "queue_stats": self.job_queue.get_queue_stats(),
            "cache_stats": self.cache.get_stats(),
        }


class ParallelSimulationExecutor:
    """Execute multiple simulations in parallel."""

    def __init__(
        self,
        simulate_func: Callable,
        max_parallel: int = 4,
        cache_results: bool = True,
    ):
        """Initialize parallel executor.
        
        Args:
            simulate_func: Function to simulate (takes params dict)
            max_parallel: Max concurrent simulations
            cache_results: Cache results after execution
        """
        self.simulate_func = simulate_func
        self.max_parallel = max_parallel
        self.cache_results = cache_results
        self.executor = ThreadPoolExecutor(max_workers=max_parallel)
        self.cache = get_cache()

    def execute_batch(
        self,
        param_list: list[dict[str, Any]],
        user_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """Execute multiple simulations in parallel.
        
        Args:
            param_list: List of parameter dicts to simulate
            user_id: Optional user ID for caching
            
        Returns:
            Dict with results and statistics
        """
        logger.info(f"⚙️  Starting parallel execution of {len(param_list)} simulations...")
        
        results = {}
        cache_hits = 0
        cache_misses = 0
        futures = {}
        
        # First check cache for all params
        for idx, params in enumerate(param_list):
            cached = self.cache.get_simulation_cache(params, user_id)
            if cached and cached.get("status") != "warming":
                results[idx] = cached
                cache_hits += 1
            else:
                # Submit to executor
                future = self.executor.submit(self.simulate_func, params)
                futures[idx] = future
                cache_misses += 1
        
        logger.info(f"💾 Cache hits: {cache_hits}, misses: {cache_misses}")
        
        # Collect results from futures
        for idx, future in futures.items():
            try:
                result = future.result(timeout=300)  # 5 minute timeout
                results[idx] = result
                
                # Cache result
                if self.cache_results:
                    params = param_list[idx]
                    self.cache.cache_simulation_result(params, result, user_id)
            
            except Exception as e:
                logger.error(f"❌ Simulation {idx} failed: {e}")
                results[idx] = {"error": str(e), "status": "failed"}
        
        # Compute statistics
        successful = sum(1 for r in results.values() if "error" not in r)
        failed = len(results) - successful
        
        summary = {
            "total_simulations": len(param_list),
            "successful": successful,
            "failed": failed,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
            "results": results,
        }
        
        logger.info(f"✅ Parallel execution complete: {successful}/{len(param_list)} successful")
        return summary

    def shutdown(self) -> None:
        """Shutdown executor."""
        self.executor.shutdown(wait=True)
        logger.info("🛑 Executor shutdown complete")


# Global worker instance
_worker: Optional[JobWorker] = None


def get_job_worker(num_workers: int = 4) -> JobWorker:
    """Get or create global job worker instance."""
    global _worker
    
    if _worker is None:
        _worker = JobWorker(num_workers=num_workers)
    
    return _worker
