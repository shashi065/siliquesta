"""
Async Task Status API Endpoints

Provides endpoints for checking background task status and results.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

from app.services.task_monitor import TaskMonitor, TaskQueue

router = APIRouter()


class TaskStatusResponse(BaseModel):
    """Task status response."""
    task_id: str
    status: str  # pending|started|success|failure|retry
    successful: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse:
    """
    Get the current status of a background task.
    
    Use this endpoint to poll for task completion.
    
    Args:
        task_id: Celery task ID returned from async endpoint
        
    Returns:
        Current task status and result (if complete)
        
    Example:
        GET /status/task/abc123.../status
        
        Response:
        {
            "task_id": "abc123...",
            "status": "success",
            "successful": true,
            "result": {
                "optimization_results": {...},
                "pareto_front": [...]
            }
        }
    """
    try:
        status_dict = TaskMonitor.get_task_status(task_id)
        return TaskStatusResponse(
            task_id=task_id,
            status=status_dict.get("status", "unknown"),
            successful=status_dict.get("successful", False),
            result=status_dict.get("result"),
            error=status_dict.get("error")
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/task/{task_id}/result")
async def get_task_result(task_id: str) -> Dict[str, Any]:
    """
    Get the result of a completed task.
    
    Returns 404 if task not found or not yet complete.
    Returns 202 if task still processing.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Task result data (varies by task type)
        
    Example:
        GET /status/task/abc123.../result
    """
    status = TaskMonitor.get_task_status(task_id)
    
    if status.get("status") == "failure":
        raise HTTPException(
            status_code=400,
            detail=f"Task failed: {status.get('error', 'Unknown error')}"
        )
    
    if not status.get("successful"):
        raise HTTPException(
            status_code=202,
            detail="Task not yet complete"
        )
    
    result = status.get("result")
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Task result not found"
        )
    
    return result


@router.get("/tasks/queue/status")
async def get_queue_status() -> Dict[str, Any]:
    """
    Get background task queue status.
    
    Returns information about worker health and queue load.
    
    Returns:
        {
            "status": "operational|degraded|offline",
            "workers_online": int,
            "active_tasks": int,
            "pending_tasks": int
        }
    """
    return TaskQueue.get_queue_status()


@router.post("/task/{task_id}/cancel")
async def cancel_task(task_id: str) -> Dict[str, str]:
    """
    Attempt to cancel a background task.
    
    May not succeed if task has already started executing.
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Cancellation status
    """
    try:
        # Celery revoke implementation
        from app.celery_app import celery_app
        if celery_app is None:
            raise HTTPException(status_code=503, detail="Celery not available")
        
        celery_app.control.revoke(task_id, terminate=True)
        return {"status": "revoked", "task_id": task_id}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )
