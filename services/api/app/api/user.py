"""User management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import ComputeJob, User

router = APIRouter()


class UserProfile(BaseModel):
    id: int
    email: str
    name: str
    plan: str
    credits_remaining: float
    created_at: str


@router.get("/me", response_model=UserProfile)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        plan=current_user.plan,
        credits_remaining=float(current_user.credits_remaining),
        created_at=current_user.created_at.isoformat(),
    )


@router.get("/{user_id}/designs")
async def get_user_designs(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if str(current_user.id) != user_id:
        return {"designs": []}
    result = await db.execute(
        select(ComputeJob)
        .where(ComputeJob.user_id == current_user.id)
        .order_by(ComputeJob.created_at.desc())
        .limit(25)
    )
    return {
        "designs": [
            {
                "job_key": job.job_key,
                "scope": job.scope,
                "status": job.status,
                "created_at": job.created_at.isoformat(),
                "result": job.result_json,
            }
            for job in result.scalars().all()
            if job.scope.startswith(("simulate", "pvt", "optimizer", "twin"))
        ]
    }
