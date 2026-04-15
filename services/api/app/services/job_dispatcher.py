"""Job dispatch helpers for sync and async compute execution."""

from __future__ import annotations

from typing import Any

from app.celery_app import celery_app
from app.config import settings

try:
    from celery.result import AsyncResult
except Exception:  # pragma: no cover - optional runtime dependency
    AsyncResult = None


class JobDispatcher:
    @staticmethod
    def celery_enabled() -> bool:
        return celery_app is not None

    @staticmethod
    def dispatch(task_name: str, *args: Any, **kwargs: Any) -> str:
        if celery_app is None:
            raise RuntimeError("Celery is not installed or configured.")
        task = celery_app.send_task(task_name, args=args, kwargs=kwargs)
        return task.id

    @staticmethod
    def status(task_id: str) -> dict[str, Any]:
        if celery_app is None or AsyncResult is None:
            raise RuntimeError("Celery is not installed or configured.")
        result = AsyncResult(task_id, app=celery_app)
        return {
            "task_id": task_id,
            "status": result.status,
            "successful": result.successful() if result.ready() else False,
            "result": result.result if result.successful() else None,
        }
