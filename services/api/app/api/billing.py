"""Billing and subscription endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.models import BillingEvent, ComputeJob, CreditLedger, Subscription, User
from app.services.saas import PLAN_POLICIES, SaaSManager
from app.services.stripe_gateway import StripeGateway, StripeGatewayError

router = APIRouter()

PLAN_PRICES_INR = {
    "FREE": 0,
    "GO": 499,
    "PRO": 1499,
    "ULTRA PRO": 4999,
    "ENTERPRISE": 0,
}


class SubscribeRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"
    provider: str = "manual"
    payment_reference: str | None = None


class CheckoutRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"
    success_url: str
    cancel_url: str


@router.get("/plans")
async def get_plans():
    return {
        "plans": [
            {
                "name": plan,
                "price_inr_monthly": PLAN_PRICES_INR.get(plan, 0),
                "credits": policy["credits"],
                "burst_per_min": policy["burst_per_min"],
                "priority": policy["priority"],
            }
            for plan, policy in PLAN_POLICIES.items()
            if plan != "GUEST"
        ]
    }


@router.get("/usage")
async def usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    jobs_result = await db.execute(
        select(
            func.count(ComputeJob.id),
            func.coalesce(func.sum(ComputeJob.cost_credits), 0.0),
        ).where(ComputeJob.user_id == current_user.id)
    )
    count, credits = jobs_result.one()
    scope_result = await db.execute(
        select(ComputeJob.scope, func.count(ComputeJob.id))
        .where(ComputeJob.user_id == current_user.id)
        .group_by(ComputeJob.scope)
        .order_by(func.count(ComputeJob.id).desc())
    )
    return {
        "user_id": current_user.id,
        "plan": current_user.plan,
        "jobs_total": int(count or 0),
        "credits_consumed": float(credits or 0.0),
        "by_scope": [{ "scope": scope, "jobs": int(job_count) } for scope, job_count in scope_result.all()],
    }


@router.post("/checkout-session")
async def create_checkout_session(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = req.plan.upper()
    if plan not in PLAN_POLICIES or plan in {"GUEST", "FREE"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Plan is not billable.")
    price = PLAN_PRICES_INR.get(plan, 0)
    try:
        session = StripeGateway.create_checkout_session(
            price_inr=price,
            plan=plan,
            customer_email=current_user.email,
            success_url=req.success_url,
            cancel_url=req.cancel_url,
            billing_cycle=req.billing_cycle,
        )
    except StripeGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    db.add(
        BillingEvent(
            user_id=current_user.id,
            event_type="checkout.session.created",
            provider="stripe",
            external_id=session.id,
            payload_json={"plan": plan, "billing_cycle": req.billing_cycle, "checkout_url": session.url},
        )
    )
    await db.commit()
    return {
        "provider": "stripe",
        "checkout_session_id": session.id,
        "checkout_url": session.url,
        "plan": plan,
        "billing_cycle": req.billing_cycle,
    }


@router.post("/webhook/stripe")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    raw = await request.body()
    signature = request.headers.get("Stripe-Signature", "")
    try:
        event = StripeGateway.verify_webhook(raw, signature)
    except StripeGatewayError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    event_type = event.get("type", "unknown")
    data_object = event.get("data", {}).get("object", {})
    customer_email = data_object.get("customer_email") or data_object.get("customer_details", {}).get("email")
    provider_ref = data_object.get("id")
    db.add(
        BillingEvent(
            user_id=None,
            event_type=event_type,
            provider="stripe",
            external_id=provider_ref,
            payload_json=event,
        )
    )
    if event_type == "checkout.session.completed" and customer_email:
        result = await db.execute(select(User).where(User.email == customer_email.lower()))
        user = result.scalar_one_or_none()
        if user is not None:
            metadata = data_object.get("metadata", {})
            plan = str(metadata.get("plan", user.plan)).upper()
            billing_cycle = str(metadata.get("billing_cycle", "monthly"))
            amount_total = int(data_object.get("amount_total", 0) or 0) / 100.0
            await SaaSManager.activate_subscription(
                db=db,
                user=user,
                plan=plan,
                billing_cycle=billing_cycle,
                provider="stripe",
                provider_ref=provider_ref,
                amount_inr=amount_total,
            )
    await db.commit()
    return {"received": True, "event_type": event_type}


@router.get("/me")
async def get_billing_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    subs = await db.execute(
        select(Subscription).where(Subscription.user_id == current_user.id).order_by(Subscription.created_at.desc())
    )
    ledger = await db.execute(
        select(CreditLedger).where(CreditLedger.user_id == current_user.id).order_by(CreditLedger.created_at.desc()).limit(25)
    )
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "plan": current_user.plan,
            "credits_remaining": current_user.credits_remaining,
        },
        "subscriptions": [
            {
                "plan": s.plan,
                "status": s.status,
                "billing_cycle": s.billing_cycle,
                "provider": s.provider,
                "provider_ref": s.provider_ref,
                "amount_inr": s.amount_inr,
                "started_at": s.started_at.isoformat(),
                "renews_at": s.renews_at.isoformat() if s.renews_at else None,
            }
            for s in subs.scalars().all()
        ],
        "ledger": [
            {
                "delta": item.delta,
                "balance_after": item.balance_after,
                "reason": item.reason,
                "scope": item.scope,
                "created_at": item.created_at.isoformat(),
            }
            for item in ledger.scalars().all()
        ],
    }


@router.post("/subscribe")
async def subscribe(
    req: SubscribeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    plan = req.plan.upper()
    if plan not in PLAN_POLICIES or plan == "GUEST":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown plan.")

    amount = PLAN_PRICES_INR.get(plan, 0)
    sub = await SaaSManager.activate_subscription(
        db=db,
        user=current_user,
        plan=plan,
        billing_cycle=req.billing_cycle,
        provider=req.provider,
        provider_ref=req.payment_reference,
        amount_inr=amount,
    )
    await db.commit()
    await db.refresh(current_user)
    return {
        "status": "active",
        "plan": current_user.plan,
        "credits_remaining": current_user.credits_remaining,
        "subscription": {
            "id": sub.id,
            "provider": sub.provider,
            "provider_ref": sub.provider_ref,
            "renews_at": sub.renews_at.isoformat() if sub.renews_at else None,
        },
    }
