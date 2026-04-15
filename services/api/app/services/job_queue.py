"""Job queue system for asynchronous simulation execution.

Supports both Redis-backed and in-memory queue modes.
Handles job scheduling, status tracking, and parallel simulation execution.
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import redis
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ComputeJob

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution states."""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    """Job priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class JobQueue:
    """Redis-backed job queue with SQLAlchemy persistence."""

    def __init__(self, redis_url: str = "redis://localhost:6379", use_redis: bool = True):
        """Initialize job queue.
        
        Args:
            redis_url: Redis connection URL
            use_redis: Use Redis if available, fallback to in-memory queue
        """
        self.use_redis = use_redis
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory_queue: dict[str, Any] = {}  # Fallback queue
        
        if use_redis:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info("✅ Connected to Redis for job queueing")
            except Exception as e:
                logger.warning(f"⚠️  Redis unavailable: {e}. Using in-memory queue.")
                self.use_redis = False

    def enqueue(
        self,
        job_type: str,
        params: dict[str, Any],
        user_id: Optional[int] = None,
        priority: JobPriority = JobPriority.NORMAL,
        db: Optional[Session] = None,
    ) -> str:
        """Enqueue a new job.
        
        Args:
            job_type: Type of job ('simulate', 'optimize', 'analyze')
            params: Job parameters
            user_id: Associated user ID
            priority: Job priority
            db: Database session for persistence
            
        Returns:
            Job ID (unique key)
        """
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        job_key = f"{job_type}:{job_id}"
        
        job_data = {
            "id": job_id,
            "type": job_type,
            "params": params,
            "priority": priority.value,
            "status": JobStatus.QUEUED.value,
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user_id,
        }
        
        # Store in Redis if available
        if self.redis_client:
            try:
                self.redis_client.hset(f"job:{job_key}", mapping=job_data)
                self.redis_client.lpush(f"queue:{priority.value}", job_key)
                logger.info(f"✅ Job enqueued: {job_key}")
            except Exception as e:
                logger.error(f"❌ Redis enqueue failed: {e}")
                self._fallback_enqueue(job_key, job_data)
        else:
            self._fallback_enqueue(job_key, job_data)
        
        # Also persist to database
        if db:
            try:
                compute_job = ComputeJob(
                    job_key=job_key,
                    user_id=user_id,
                    scope=job_type,
                    status=JobStatus.QUEUED.value,
                    priority=priority.value,
                    request_json=params,
                )
                db.add(compute_job)
                db.commit()
            except Exception as e:
                logger.warning(f"⚠️  Failed to persist job to database: {e}")
        
        return job_key

    def dequeue(self, priority_only: Optional[JobPriority] = None) -> Optional[tuple[str, dict[str, Any]]]:
        """Dequeue next job for processing.
        
        Args:
            priority_only: If set, only dequeue from this priority level
            
        Returns:
            Tuple of (job_key, job_data) or None
        """
        if not self.redis_client:
            return self._fallback_dequeue(priority_only)
        
        try:
            # Try priorities: urgent, high, normal, low
            priorities = [JobPriority.URGENT.value, JobPriority.HIGH.value, 
                         JobPriority.NORMAL.value, JobPriority.LOW.value]
            
            if priority_only:
                priorities = [priority_only.value]
            
            for priority in priorities:
                queue_key = f"queue:{priority}"
                job_key = self.redis_client.rpop(queue_key)
                
                if job_key:
                    job_data = self.redis_client.hgetall(f"job:{job_key}")
                    if job_data:
                        job_data["status"] = JobStatus.RUNNING.value
                        job_data["started_at"] = datetime.utcnow().isoformat()
                        self.redis_client.hset(f"job:{job_key}", mapping=job_data)
                        logger.info(f"✅ Job dequeued: {job_key}")
                        return (job_key, job_data)
            
            return None
        except Exception as e:
            logger.error(f"❌ Redis dequeue failed: {e}")
            return self._fallback_dequeue(priority_only)

    def get_status(self, job_key: str) -> Optional[dict[str, Any]]:
        """Get job status.
        
        Args:
            job_key: Job identifier
            
        Returns:
            Job data or None
        """
        if self.redis_client:
            try:
                job_data = self.redis_client.hgetall(f"job:{job_key}")
                if job_data:
                    return job_data
            except Exception as e:
                logger.warning(f"⚠️  Redis status lookup failed: {e}")
        
        # Fallback to in-memory or database
        if job_key in self.in_memory_queue:
            return self.in_memory_queue[job_key]
        
        return None

    def mark_completed(
        self,
        job_key: str,
        result: dict[str, Any],
        db: Optional[Session] = None,
    ) -> bool:
        """Mark job as completed with result.
        
        Args:
            job_key: Job identifier
            result: Job result data
            db: Database session
            
        Returns:
            Success flag
        """
        try:
            if self.redis_client:
                self.redis_client.hset(
                    f"job:{job_key}",
                    mapping={
                        "status": JobStatus.COMPLETED.value,
                        "result": json.dumps(result),
                        "finished_at": datetime.utcnow().isoformat(),
                    },
                )
                # TTL: keep completed jobs for 24 hours
                self.redis_client.expire(f"job:{job_key}", 86400)
            else:
                if job_key in self.in_memory_queue:
                    self.in_memory_queue[job_key]["status"] = JobStatus.COMPLETED.value
                    self.in_memory_queue[job_key]["result"] = result
                    self.in_memory_queue[job_key]["finished_at"] = datetime.utcnow().isoformat()
            
            # Update database
            if db:
                stmt = select(ComputeJob).where(ComputeJob.job_key == job_key)
                job = db.scalars(stmt).first()
                if job:
                    job.status = JobStatus.COMPLETED.value
                    job.result_json = result
                    job.finished_at = datetime.utcnow()
                    db.commit()
            
            logger.info(f"✅ Job completed: {job_key}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark job completed: {e}")
            return False

    def mark_failed(
        self,
        job_key: str,
        error: str,
        db: Optional[Session] = None,
    ) -> bool:
        """Mark job as failed with error message.
        
        Args:
            job_key: Job identifier
            error: Error description
            db: Database session
            
        Returns:
            Success flag
        """
        try:
            if self.redis_client:
                self.redis_client.hset(
                    f"job:{job_key}",
                    mapping={
                        "status": JobStatus.FAILED.value,
                        "error": error,
                        "finished_at": datetime.utcnow().isoformat(),
                    },
                )
                self.redis_client.expire(f"job:{job_key}", 86400)
            else:
                if job_key in self.in_memory_queue:
                    self.in_memory_queue[job_key]["status"] = JobStatus.FAILED.value
                    self.in_memory_queue[job_key]["error"] = error
                    self.in_memory_queue[job_key]["finished_at"] = datetime.utcnow().isoformat()
            
            # Update database
            if db:
                stmt = select(ComputeJob).where(ComputeJob.job_key == job_key)
                job = db.scalars(stmt).first()
                if job:
                    job.status = JobStatus.FAILED.value
                    job.error_text = error
                    job.finished_at = datetime.utcnow()
                    db.commit()
            
            logger.error(f"❌ Job failed: {job_key} - {error}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to mark job failed: {e}")
            return False

    def get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics.
        
        Returns:
            Queue statistics
        """
        stats = {
            "total_jobs": 0,
            "queued": 0,
            "running": 0,
            "completed": 0,
            "failed": 0,
        }
        
        if self.redis_client:
            try:
                for priority in [p.value for p in JobPriority]:
                    queue_len = self.redis_client.llen(f"queue:{priority}")
                    stats["queued"] += queue_len
                
                # Estimate from database would be more accurate but slower
                stats["total_jobs"] = stats["queued"]
            except Exception as e:
                logger.warning(f"⚠️  Failed to get queue stats: {e}")
        else:
            stats["total_jobs"] = len(self.in_memory_queue)
            stats["queued"] = sum(1 for job in self.in_memory_queue.values() 
                                if job.get("status") == JobStatus.QUEUED.value)
            stats["running"] = sum(1 for job in self.in_memory_queue.values() 
                                 if job.get("status") == JobStatus.RUNNING.value)
            stats["completed"] = sum(1 for job in self.in_memory_queue.values() 
                                   if job.get("status") == JobStatus.COMPLETED.value)
            stats["failed"] = sum(1 for job in self.in_memory_queue.values() 
                               if job.get("status") == JobStatus.FAILED.value)
        
        return stats

    # ============ Private Methods ============

    def _fallback_enqueue(self, job_key: str, job_data: dict[str, Any]) -> None:
        """Fallback: enqueue to in-memory dictionary."""
        self.in_memory_queue[job_key] = job_data
        logger.info(f"📝 Job stored in-memory: {job_key}")

    def _fallback_dequeue(
        self,
        priority_only: Optional[JobPriority] = None,
    ) -> Optional[tuple[str, dict[str, Any]]]:
        """Fallback: dequeue from in-memory dictionary."""
        # Simple FIFO from in-memory queue
        for job_key, job_data in list(self.in_memory_queue.items()):
            if job_data.get("status") == JobStatus.QUEUED.value:
                if priority_only and job_data.get("priority") != priority_only.value:
                    continue
                
                job_data["status"] = JobStatus.RUNNING.value
                job_data["started_at"] = datetime.utcnow().isoformat()
                return (job_key, job_data)
        
        return None


# Global job queue instance
_job_queue: Optional[JobQueue] = None


def get_job_queue(redis_url: str = "redis://localhost:6379") -> JobQueue:
    """Get or create global job queue instance."""
    global _job_queue
    
    if _job_queue is None:
        _job_queue = JobQueue(redis_url=redis_url)
    
    return _job_queue
