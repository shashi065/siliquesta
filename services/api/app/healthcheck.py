"""Runtime health checks for core services."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.celery_app import celery_app
from app.database import database_healthcheck


@dataclass
class HealthStatus:
    ok: bool
    detail: str | None = None


async def check_redis() -> HealthStatus:
    try:
        import redis.asyncio as redis_async  # type: ignore

        client = redis_async.from_url(
            celery_app.conf.broker_url if celery_app is not None else "redis://localhost:6379",
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        await client.close()
        return HealthStatus(ok=True)
    except Exception as exc:  # pragma: no cover - runtime check
        return HealthStatus(ok=False, detail=str(exc))


def check_celery_workers() -> HealthStatus:
    if celery_app is None:
        return HealthStatus(ok=False, detail="Celery not configured.")
    try:
        inspect = celery_app.control.inspect(timeout=2.0)
        ping = inspect.ping() if inspect is not None else None
        if not ping:
            return HealthStatus(ok=False, detail="No Celery workers responded.")
        return HealthStatus(ok=True)
    except Exception as exc:  # pragma: no cover - runtime check
        return HealthStatus(ok=False, detail=str(exc))


def check_ml_stack() -> HealthStatus:
    try:
        import torch  # noqa: F401
        import xgboost  # noqa: F401
        import optuna  # noqa: F401
        return HealthStatus(ok=True)
    except Exception as exc:
        return HealthStatus(ok=False, detail=str(exc))


async def check_database() -> HealthStatus:
    status = await database_healthcheck()
    if status.get("status") == "ok":
        return HealthStatus(ok=True)
    return HealthStatus(ok=False, detail=status.get("detail"))


async def assert_startup_dependencies(timeout: float = 30.0) -> None:
    redis_status = await check_redis()
    if not redis_status.ok:
        raise RuntimeError(f"Redis unavailable: {redis_status.detail}")
    db_status = await check_database()
    if not db_status.ok:
        raise RuntimeError(f"Database unavailable: {db_status.detail}")

    # Wait briefly for Celery workers to come online
    deadline = asyncio.get_event_loop().time() + timeout
    celery_status = check_celery_workers()
    while not celery_status.ok and asyncio.get_event_loop().time() < deadline:
        await asyncio.sleep(2.0)
        celery_status = check_celery_workers()
    if not celery_status.ok:
        raise RuntimeError(f"Celery unavailable: {celery_status.detail}")


async def gather_health() -> dict[str, dict[str, str]]:
    db = await check_database()
    redis_status = await check_redis()
    celery_status = check_celery_workers()
    ml_status = check_ml_stack()
    return {
        "db": {"status": "ok" if db.ok else "error", "detail": db.detail or ""},
        "redis": {"status": "ok" if redis_status.ok else "error", "detail": redis_status.detail or ""},
        "celery": {"status": "ok" if celery_status.ok else "error", "detail": celery_status.detail or ""},
        "ml": {"status": "ok" if ml_status.ok else "missing", "detail": ml_status.detail or ""},
    }
