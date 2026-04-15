"""API middleware for tracking usage and enforcing rate limits."""

from __future__ import annotations

import time
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings


class APITrackingMiddleware(BaseHTTPMiddleware):
    """Middleware to track API calls and performance."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track API call metrics."""
        start_time = time.time()

        # Extract user info from token if available
        user_id = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from app.services.saas_infrastructure import JWTManager

            token = auth_header.split(" ")[1]
            user_id = JWTManager.get_user_id_from_token(token)

        # Call next handler
        response = await call_next(request)

        # Calculate timing
        duration_ms = (time.time() - start_time) * 1000

        # Add metrics headers
        response.headers["X-Process-Time"] = str(duration_ms)
        response.headers["X-Request-ID"] = request.headers.get("x-request-id", "")

        # Log if enabled
        if settings.metrics_enabled:
            path = request.url.path
            method = request.method
            status = response.status_code

            log_entry = {
                "path": path,
                "method": method,
                "status": status,
                "duration_ms": duration_ms,
                "user_id": user_id,
                "client": request.client.host if request.client else None,
            }

            # Store metrics if monitoring is enabled
            try:
                import logging

                logger = logging.getLogger("api.tracking")
                logger.info(f"API request: {log_entry}")
            except Exception:
                pass

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits based on plan."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits before processing request."""
        from app.services.saas_infrastructure import RateLimitPolicy

        # Get user from token if available
        user_id = None
        plan = "GUEST"
        auth_header = request.headers.get("authorization", "")

        if auth_header.startswith("Bearer "):
            from app.services.saas_infrastructure import JWTManager

            token = auth_header.split(" ")[1]
            user_id = JWTManager.get_user_id_from_token(token)
            payload = JWTManager.decode_token(token)
            if payload:
                plan = payload.get("plan", "FREE")

        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Check rate limit
        if user_id:
            redis_client = None
            try:
                import redis.asyncio as redis_async

                redis_client = redis_async.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            except Exception:
                pass

            allowed, info = await RateLimitPolicy.check_rate_limit(redis_client, user_id, plan)

            if not allowed:
                from fastapi import HTTPException, status

                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. {info.get('reason')}",
                )

        return await call_next(request)


class UserIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce user isolation."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Enforce user isolation checks."""
        # User isolation is enforced in individual endpoints
        # This middleware could add additional checks if needed

        return await call_next(request)
