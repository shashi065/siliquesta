"""SaaS policy, credits, jobs, and rate limiting for SILIQUESTA."""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ComputeJob, CreditLedger, RateLimitEvent, Subscription, User


PLAN_POLICIES: dict[str, dict[str, Any]] = {
    "GUEST": {"credits": 25.0, "burst_per_min": 8, "priority": "low"},
    "FREE": {"credits": 200.0, "burst_per_min": 20, "priority": "low"},
    "GO": {"credits": 2000.0, "burst_per_min": 80, "priority": "normal"},
    "PRO": {"credits": 8000.0, "burst_per_min": 200, "priority": "high"},
    "ULTRA PRO": {"credits": 25000.0, "burst_per_min": 500, "priority": "high"},
    "ENTERPRISE": {"credits": 100000.0, "burst_per_min": 2000, "priority": "enterprise"},
}

SCOPE_COSTS: dict[str, float] = {
    "simulate.run": 4.0,
    "simulate.batch": 8.0,
    "pvt.corner-summary": 8.0,
    "pvt.full-sweep": 24.0,
    "optimizer.run": 20.0,
    "twin.predict": 6.0,
    "twin.compute-aging": 4.0,
    "ai.chat": 2.0,
    "ai.generate-code": 4.0,
    "ai.predict-failure": 3.0,
}

_rate_windows: dict[str, deque[float]] = defaultdict(deque)
_redis_client = None
_redis_unavailable = False


@dataclass
class AccessContext:
    actor_key: str
    plan: str
    priority: str
    user: User | None
    available_credits: float
    cost_credits: float


class SaaSManager:
    @staticmethod
    async def _get_redis():
        global _redis_client, _redis_unavailable
        if _redis_unavailable:
            return None
        if _redis_client is not None:
            return _redis_client
        try:
            import redis.asyncio as redis_async

            _redis_client = redis_async.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
            await _redis_client.ping()
            return _redis_client
        except Exception:
            _redis_unavailable = True
            _redis_client = None
            return None

    @staticmethod
    def policy_for(plan: str | None) -> dict[str, Any]:
        return PLAN_POLICIES.get((plan or "GUEST").upper(), PLAN_POLICIES["FREE"])

    @staticmethod
    def request_actor(request: Request, user: User | None) -> str:
        if user is not None:
            return f"user:{user.id}"
        forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        host = forwarded or (request.client.host if request.client else "guest")
        return f"guest:{host}"

    @classmethod
    async def authorize(
        cls,
        db: AsyncSession,
        request: Request,
        scope: str,
        user: User | None = None,
        cost_credits: float | None = None,
    ) -> AccessContext:
        plan = (user.plan if user is not None else "GUEST").upper()
        policy = cls.policy_for(plan)
        actor_key = cls.request_actor(request, user)
        cost = cost_credits if cost_credits is not None else SCOPE_COSTS.get(scope, 1.0)
        await cls._check_rate_limit(actor_key, scope, policy["burst_per_min"])
        db.add(RateLimitEvent(actor_key=actor_key, scope=scope, plan=plan))

        available = user.credits_remaining if user is not None else policy["credits"]
        if available < cost:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Not enough compute credits for {scope}. Required {cost:.1f}, available {available:.1f}.",
            )

        return AccessContext(
            actor_key=actor_key,
            plan=plan,
            priority=policy["priority"],
            user=user,
            available_credits=available,
            cost_credits=cost,
        )

    @classmethod
    async def _check_rate_limit(cls, actor_key: str, scope: str, per_minute: int) -> None:
        now = datetime.utcnow().timestamp()
        bucket_key = f"{actor_key}:{scope}"
        redis_client = await cls._get_redis()
        if redis_client is not None:
            cutoff = now - 60
            try:
                await redis_client.zremrangebyscore(bucket_key, 0, cutoff)
                current_count = int(await redis_client.zcard(bucket_key))
                if current_count >= per_minute:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit reached for {scope}. Try again shortly.",
                    )
                await redis_client.zadd(bucket_key, {f"{now}:{uuid4().hex}": now})
                await redis_client.expire(bucket_key, 120)
                return
            except HTTPException:
                raise
            except Exception:
                # Fall back to in-process limiting if Redis is down or unreachable.
                pass

        bucket = _rate_windows[bucket_key]
        cutoff = now - 60
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit reached for {scope}. Try again shortly.",
            )
        bucket.append(now)

    @staticmethod
    async def consume_credits(
        db: AsyncSession,
        user: User | None,
        amount: float,
        scope: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if user is None or amount <= 0:
            return
        user.credits_remaining = max(0.0, float(user.credits_remaining) - amount)
        db.add(
            CreditLedger(
                user_id=user.id,
                delta=-amount,
                balance_after=user.credits_remaining,
                reason="compute",
                scope=scope,
                metadata_json=metadata or {},
            )
        )

    @staticmethod
    async def grant_plan_credits(db: AsyncSession, user: User, reason: str = "plan-activation") -> None:
        credits = float(SaaSManager.policy_for(user.plan)["credits"])
        user.credits_remaining = credits
        db.add(
            CreditLedger(
                user_id=user.id,
                delta=credits,
                balance_after=credits,
                reason=reason,
                scope="billing",
                metadata_json={"plan": user.plan},
            )
        )

    @staticmethod
    async def activate_subscription(
        db: AsyncSession,
        user: User,
        plan: str,
        billing_cycle: str = "monthly",
        provider: str = "manual",
        provider_ref: str | None = None,
        amount_inr: float = 0.0,
    ) -> Subscription:
        plan = plan.upper()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == user.id, Subscription.status == "active")
        )
        for existing in result.scalars().all():
            existing.status = "replaced"
        sub = Subscription(
            user_id=user.id,
            plan=plan,
            status="active",
            billing_cycle=billing_cycle,
            provider=provider,
            provider_ref=provider_ref,
            amount_inr=amount_inr,
            renews_at=datetime.utcnow() + timedelta(days=30 if billing_cycle == "monthly" else 365),
        )
        user.plan = plan
        db.add(sub)
        await SaaSManager.grant_plan_credits(db, user)
        return sub

    @staticmethod
    async def create_job(
        db: AsyncSession,
        scope: str,
        user: User | None,
        request_payload: dict[str, Any] | None,
        priority: str,
        cost_credits: float,
    ) -> ComputeJob:
        job = ComputeJob(
            job_key=uuid4().hex,
            user_id=user.id if user else None,
            scope=scope,
            status="queued",
            priority=priority,
            cost_credits=cost_credits,
            request_json=request_payload or {},
        )
        db.add(job)
        await db.flush()
        return job

    @staticmethod
    async def attach_task_id(job: ComputeJob, task_id: str) -> None:
        job.backend_task_id = task_id

    @staticmethod
    async def start_job(job: ComputeJob) -> None:
        job.status = "running"
        job.started_at = datetime.utcnow()

    @staticmethod
    async def complete_job(job: ComputeJob, result_payload: dict[str, Any] | None = None) -> None:
        job.status = "completed"
        job.finished_at = datetime.utcnow()
        job.result_json = result_payload or {}

    @staticmethod
    async def fail_job(job: ComputeJob, error_text: str, retry_count: int | None = None) -> None:
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        job.error_text = error_text[:4000]
        if retry_count is not None:
            job.retry_count = retry_count
