"""Celery application for async simulation, AI, and ML jobs."""

from __future__ import annotations

from app.config import settings

try:
    from celery import Celery
except Exception:  # pragma: no cover - optional runtime dependency
    Celery = None


if Celery is not None:
    celery_app = Celery(
        "siliquesta",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
        include=["app.tasks.compute"],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        result_expires=86400,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
        broker_connection_retry_on_startup=True,
        task_time_limit=300,
        task_soft_time_limit=240,
    )
else:  # pragma: no cover - optional runtime dependency
    celery_app = None
