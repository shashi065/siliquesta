"""Enhanced SaaS infrastructure: authentication, usage tracking, and credit system."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import ComputeJob, CreditLedger, User


class JWTManager:
    """JWT token management with expiration and refresh."""

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """Decode JWT token safely."""
        from jose import JWTError, jwt

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            return payload
        except JWTError:
            return None

    @staticmethod
    def encode_token(
        data: dict[str, Any],
        expires_delta: timedelta | None = None,
    ) -> str:
        """Encode JWT token with expiration."""
        from jose import jwt

        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        to_encode.update({"exp": expire, "iat": datetime.utcnow()})
        return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if token is expired."""
        payload = JWTManager.decode_token(token)
        if not payload:
            return True

        exp = payload.get("exp")
        if not exp:
            return True

        return datetime.utcfromtimestamp(exp) < datetime.utcnow()

    @staticmethod
    def get_user_id_from_token(token: str) -> int | None:
        """Extract user ID from token."""
        payload = JWTManager.decode_token(token)
        return payload.get("uid") if payload else None


class UsageTracker:
    """Track API usage per user, project, and operation."""

    @staticmethod
    async def track_api_call(
        db: AsyncSession,
        user: User | None,
        scope: str,
        credits_charged: float,
        metadata: dict[str, Any] | None = None,
        project_id: int | None = None,
    ) -> None:
        """
        Record an API call in usage tracking.

        Args:
            db: Database session
            user: User making the call (may be None)
            scope: Operation scope (e.g., "optimizer.run", "twin.predict")
            credits_charged: Credit amount deducted
            metadata: Additional tracking info
            project_id: Associated project ID
        """
        if not user:
            return

        tracking_data = {
            "scope": scope,
            "credits": credits_charged,
            "timestamp": datetime.utcnow().isoformat(),
            **(metadata or {}),
        }

        ledger = CreditLedger(
            user_id=user.id,
            delta=-credits_charged,
            balance_after=user.credits_remaining,
            reason="compute",
            scope=scope,
            metadata_json=tracking_data,
        )
        db.add(ledger)

    @staticmethod
    async def get_usage_summary(
        db: AsyncSession,
        user: User,
        days: int = 30,
        scope: str | None = None,
    ) -> dict[str, Any]:
        """
        Get usage summary for a user over specified period.

        Args:
            db: Database session
            user: User to get stats for
            days: Number of days to look back
            scope: Optional specific scope to filter

        Returns:
            Dict with usage stats
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(CreditLedger).where(
            and_(
                CreditLedger.user_id == user.id,
                CreditLedger.created_at >= cutoff,
                CreditLedger.reason == "compute",
            )
        )

        if scope:
            query = query.where(CreditLedger.scope == scope)

        result = await db.execute(query)
        ledgers = result.scalars().all()

        # Group by scope
        scope_usage = {}
        total_credits = 0.0
        call_count = 0

        for ledger in ledgers:
            scope_name = ledger.scope or "unknown"
            if scope_name not in scope_usage:
                scope_usage[scope_name] = {"calls": 0, "credits": 0.0}

            scope_usage[scope_name]["calls"] += 1
            scope_usage[scope_name]["credits"] += abs(ledger.delta)
            total_credits += abs(ledger.delta)
            call_count += 1

        return {
            "user_id": user.id,
            "period_days": days,
            "total_calls": call_count,
            "total_credits_used": round(total_credits, 2),
            "average_credits_per_call": round(total_credits / call_count if call_count > 0 else 0, 4),
            "by_scope": scope_usage,
            "start_date": cutoff.isoformat(),
            "end_date": datetime.utcnow().isoformat(),
        }

    @staticmethod
    async def get_daily_usage(
        db: AsyncSession,
        user: User,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """Get daily usage breakdown."""
        cutoff = datetime.utcnow() - timedelta(days=days)

        query = select(CreditLedger).where(
            and_(
                CreditLedger.user_id == user.id,
                CreditLedger.created_at >= cutoff,
                CreditLedger.reason == "compute",
            )
        )

        result = await db.execute(query)
        ledgers = result.scalars().all()

        # Group by day
        daily = {}
        for ledger in ledgers:
            day = ledger.created_at.date().isoformat()
            if day not in daily:
                daily[day] = {"calls": 0, "credits": 0.0}

            daily[day]["calls"] += 1
            daily[day]["credits"] += abs(ledger.delta)

        return [
            {
                "date": date,
                **stats,
            }
            for date, stats in sorted(daily.items())
        ]


class CreditManager:
    """Manage credit allocation, consumption, and refunds."""

    PLAN_CREDITS: dict[str, float] = {
        "GUEST": 25.0,
        "FREE": 200.0,
        "GO": 2000.0,
        "PRO": 8000.0,
        "ULTRA PRO": 25000.0,
        "ENTERPRISE": 100000.0,
    }

    OPERATION_COSTS: dict[str, float] = {
        "optimizer.run": 20.0,
        "optimizer.batch": 50.0,
        "twin.predict": 6.0,
        "twin.train": 30.0,
        "twin.explain": 2.0,
        "twin.compute-aging": 4.0,
        "simulate.run": 4.0,
        "simulate.batch": 8.0,
        "pvt.sweep": 12.0,
        "memory.search": 0.5,
        "memory.batch-search": 2.0,
        "ai.chat": 2.0,
        "ai.orchestrate": 10.0,
    }

    @staticmethod
    def get_operation_cost(scope: str, custom_cost: float | None = None) -> float:
        """Get cost for an operation."""
        if custom_cost is not None and custom_cost > 0:
            return custom_cost
        return CreditManager.OPERATION_COSTS.get(scope, 1.0)

    @staticmethod
    def get_plan_credits(plan: str) -> float:
        """Get initial credits for a plan."""
        return CreditManager.PLAN_CREDITS.get(plan.upper(), 200.0)

    @staticmethod
    async def allocate_plan_credits(
        db: AsyncSession,
        user: User,
        reason: str = "plan_activation",
    ) -> None:
        """
        Allocate credits for a plan upgrade/change.

        Args:
            db: Database session
            user: User to allocate credits for
            reason: Reason for allocation
        """
        credits = CreditManager.get_plan_credits(user.plan)
        user.credits_remaining = Decimal(str(credits))

        ledger = CreditLedger(
            user_id=user.id,
            delta=credits,
            balance_after=float(user.credits_remaining),
            reason=reason,
            scope="billing",
            metadata_json={"plan": user.plan, "action": "allocation"},
        )
        db.add(ledger)

    @staticmethod
    async def charge_credits(
        db: AsyncSession,
        user: User | None,
        amount: float,
        scope: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Charge credits for an operation.

        Args:
            db: Database session
            user: User to charge (may be None)
            amount: Amount to charge
            scope: Operation scope
            metadata: Additional metadata
        """
        if not user or amount <= 0:
            return

        user.credits_remaining = max(0.0, float(user.credits_remaining) - amount)

        ledger = CreditLedger(
            user_id=user.id,
            delta=-amount,
            balance_after=float(user.credits_remaining),
            reason="compute",
            scope=scope,
            metadata_json=metadata or {},
        )
        db.add(ledger)

        # Track usage
        await UsageTracker.track_api_call(
            db=db,
            user=user,
            scope=scope,
            credits_charged=amount,
            metadata=metadata,
        )

    @staticmethod
    async def refund_credits(
        db: AsyncSession,
        user: User,
        amount: float,
        reason: str = "refund",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Refund credits to user.

        Args:
            db: Database session
            user: User to refund
            amount: Amount to refund
            reason: Reason for refund
            metadata: Additional metadata
        """
        if amount <= 0:
            return

        user.credits_remaining = float(user.credits_remaining) + amount

        ledger = CreditLedger(
            user_id=user.id,
            delta=amount,
            balance_after=float(user.credits_remaining),
            reason=reason,
            scope="refund",
            metadata_json=metadata or {},
        )
        db.add(ledger)

    @staticmethod
    async def get_credit_history(
        db: AsyncSession,
        user: User,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """Get user's credit transaction history."""
        query = select(CreditLedger).where(CreditLedger.user_id == user.id).order_by(
            CreditLedger.created_at.desc()
        )

        result = await db.execute(query.offset(offset).limit(limit))
        ledgers = result.scalars().all()

        return [
            {
                "id": ledger.id,
                "timestamp": ledger.created_at.isoformat(),
                "delta": float(ledger.delta),
                "balance_after": float(ledger.balance_after) if ledger.balance_after else 0.0,
                "reason": ledger.reason,
                "scope": ledger.scope,
                "metadata": ledger.metadata_json or {},
            }
            for ledger in ledgers
        ]

    @staticmethod
    async def get_balance(db: AsyncSession, user: User) -> dict[str, Any]:
        """Get current credit balance and plan info."""
        return {
            "user_id": user.id,
            "plan": user.plan,
            "credits_remaining": float(user.credits_remaining),
            "plan_credits": CreditManager.get_plan_credits(user.plan),
            "percent_used": round(
                (1.0 - (float(user.credits_remaining) / CreditManager.get_plan_credits(user.plan))) * 100,
                1,
            ),
        }


class UserIsolationValidator:
    """Validate user isolation and access control."""

    @staticmethod
    async def validate_project_access(
        db: AsyncSession,
        user: User,
        project_id: int,
        require_edit: bool = False,
    ) -> bool:
        """
        Check if user has access to project.

        Args:
            db: Database session
            user: User requesting access
            project_id: Project ID to access
            require_edit: If True, require edit permission

        Returns:
            True if access granted
        """
        from app.models import Project, ProjectShare

        # Check direct ownership
        result = await db.execute(select(Project).where(Project.id == project_id, Project.user_id == user.id))
        if result.scalar_one_or_none():
            return True

        # Check shared access
        result = await db.execute(
            select(ProjectShare).where(
                ProjectShare.project_id == project_id,
                ProjectShare.collaborator_id == user.id,
            )
        )
        share = result.scalar_one_or_none()

        if not share:
            return False

        if require_edit and not share.can_edit:
            return False

        return True

    @staticmethod
    async def validate_job_access(
        db: AsyncSession,
        user: User,
        job_id: int | str,
    ) -> bool:
        """Check if user has access to job."""
        if isinstance(job_id, str):
            result = await db.execute(select(ComputeJob).where(ComputeJob.job_key == job_id))
        else:
            result = await db.execute(select(ComputeJob).where(ComputeJob.id == job_id))

        job = result.scalar_one_or_none()
        if not job:
            return False

        # Job belongs to user or no user (guest job)
        return job.user_id is None or job.user_id == user.id

    @staticmethod
    async def enforce_project_access(
        db: AsyncSession,
        user: User,
        project_id: int,
        require_edit: bool = False,
    ) -> None:
        """
        Enforce project access, raise if denied.

        Args:
            db: Database session
            user: User requesting access
            project_id: Project ID
            require_edit: Require edit permission

        Raises:
            HTTPException if access denied
        """
        has_access = await UserIsolationValidator.validate_project_access(
            db=db,
            user=user,
            project_id=project_id,
            require_edit=require_edit,
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this resource.",
            )

    @staticmethod
    async def enforce_job_access(
        db: AsyncSession,
        user: User,
        job_id: int | str,
    ) -> None:
        """Enforce job access, raise if denied."""
        has_access = await UserIsolationValidator.validate_job_access(
            db=db,
            user=user,
            job_id=job_id,
        )

        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this resource.",
            )


class RateLimitPolicy:
    """Rate limiting policies by plan."""

    PLAN_LIMITS: dict[str, dict[str, Any]] = {
        "GUEST": {"requests_per_min": 8, "requests_per_hour": 100},
        "FREE": {"requests_per_min": 20, "requests_per_hour": 1000},
        "GO": {"requests_per_min": 80, "requests_per_hour": 5000},
        "PRO": {"requests_per_min": 200, "requests_per_hour": 10000},
        "ULTRA PRO": {"requests_per_min": 500, "requests_per_hour": 50000},
        "ENTERPRISE": {"requests_per_min": 2000, "requests_per_hour": 100000},
    }

    @staticmethod
    def get_limits(plan: str) -> dict[str, int]:
        """Get rate limits for a plan."""
        return RateLimitPolicy.PLAN_LIMITS.get(plan.upper(), RateLimitPolicy.PLAN_LIMITS["FREE"])

    @staticmethod
    async def check_rate_limit(
        redis_client: Any,
        user_id: int,
        plan: str,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Check if user is within rate limits.

        Args:
            redis_client: Redis client
            user_id: User ID
            plan: User plan

        Returns:
            (allowed, info_dict)
        """
        if not redis_client:
            return True, {"limited": False}

        limits = RateLimitPolicy.get_limits(plan)
        key_min = f"ratelimit:user:{user_id}:min"
        key_hour = f"ratelimit:user:{user_id}:hour"

        try:
            current_min = int(await redis_client.get(key_min) or 0)
            current_hour = int(await redis_client.get(key_hour) or 0)

            if current_min >= limits["requests_per_min"] or current_hour >= limits["requests_per_hour"]:
                return False, {
                    "limited": True,
                    "reason": "rate_limit_exceeded",
                    "current_per_min": current_min,
                    "limit_per_min": limits["requests_per_min"],
                }

            # Increment counters
            await redis_client.incr(key_min)
            await redis_client.expire(key_min, 60)
            await redis_client.incr(key_hour)
            await redis_client.expire(key_hour, 3600)

            return True, {"limited": False}

        except Exception:
            # If Redis fails, allow request
            return True, {"limited": False}
