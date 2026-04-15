"""Structured app metrics and request instrumentation."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from threading import Lock

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


logger = logging.getLogger("siliquesta.observability")


@dataclass
class RequestMetric:
    count: int = 0
    errors: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = Lock()
        self._by_route: dict[str, RequestMetric] = defaultdict(RequestMetric)
        self._recent_errors: deque[dict] = deque(maxlen=100)

    def record(self, route_key: str, duration_ms: float, status_code: int) -> None:
        with self._lock:
            metric = self._by_route[route_key]
            metric.count += 1
            metric.total_ms += duration_ms
            metric.max_ms = max(metric.max_ms, duration_ms)
            if status_code >= 500:
                metric.errors += 1
                self._recent_errors.append(
                    {"route": route_key, "status_code": status_code, "duration_ms": round(duration_ms, 3)}
                )

    def snapshot(self) -> dict:
        with self._lock:
            routes = {
                route: {
                    "count": metric.count,
                    "errors": metric.errors,
                    "avg_ms": round(metric.total_ms / metric.count, 3) if metric.count else 0.0,
                    "max_ms": round(metric.max_ms, 3),
                }
                for route, metric in sorted(self._by_route.items())
            }
            return {
                "routes": routes,
                "recent_errors": list(self._recent_errors),
            }


metrics_registry = MetricsRegistry()


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - started) * 1000.0
        route_key = f"{request.method} {request.url.path}"
        metrics_registry.record(route_key, duration_ms, response.status_code)
        logger.info(
            "request.complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3),
            },
        )
        return response
