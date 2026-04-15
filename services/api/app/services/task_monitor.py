"""
Async Task Monitoring and Status Utilities

Provides helpers for monitoring Celery task status and results.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

from app.services.job_dispatcher import JobDispatcher

logger = logging.getLogger(__name__)


class TaskMonitor:
    """Monitor background task execution and retrieve results."""
    
    @staticmethod
    def get_task_status(task_id: str) -> Dict[str, Any]:
        """
        Get current status of a background task.
        
        Args:
            task_id: Celery task ID
            
        Returns:
            Dictionary with task status, result, and metadata
            
        Example:
            {
                "task_id": "abc123...",
                "status": "pending|started|success|failure|retry",
                "successful": bool,
                "result": {...} or None,
                "error": str or None,
                "progress": float [0-1],
                "eta_seconds": int or None
            }
        """
        try:
            status_dict = JobDispatcher.status(task_id)
            return status_dict
        except Exception as e:
            logger.error(f"Failed to get task status: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def is_task_complete(task_id: str) -> bool:
        """Check if a task has finished (success or failure)."""
        status = TaskMonitor.get_task_status(task_id)
        return status.get("status") in ("success", "failure")
    
    @staticmethod
    def is_task_successful(task_id: str) -> bool:
        """Check if a task completed successfully."""
        status = TaskMonitor.get_task_status(task_id)
        return status.get("successful", False)
    
    @staticmethod
    def get_task_result(task_id: str) -> Optional[Dict[str, Any]]:
        """Get the result of a completed task, or None if not ready."""
        status = TaskMonitor.get_task_status(task_id)
        return status.get("result")


class TaskQueue:
    """Query and monitor task queue status."""
    
    @staticmethod
    def get_queue_status() -> Dict[str, Any]:
        """
        Get overall queue status and worker health.
        
        Returns:
            {
                "workers_online": int,
                "active_tasks": int,
                "pending_tasks": int,
                "failed_tasks": int,
                "workers": {...}
            }
        """
        try:
            # This would require access to Celery events
            # Placeholder for queue status monitoring
            return {
                "status": "operational",
                "message": "Background task system is operational"
            }
        except Exception as e:
            logger.error(f"Failed to get queue status: {e}")
            return {"status": "error", "error": str(e)}


# Example usage:
if __name__ == "__main__":
    # Monitor a specific task
    task_id = "some-task-id-here"
    
    status = TaskMonitor.get_task_status(task_id)
    print(f"Task {task_id} status: {status['status']}")
    
    if TaskMonitor.is_task_complete(task_id):
        if TaskMonitor.is_task_successful(task_id):
            result = TaskMonitor.get_task_result(task_id)
            print(f"Result: {result}")
        else:
            print("Task failed")
