"""API key endpoints for automated access."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import APIKey, User
from app.services.api_keys import APIKeyService

router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] = ["api:*"]


@router.get("")
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc()))
    return {
        "keys": [
            {
                "id": item.id,
                "name": item.name,
                "key_prefix": item.key_prefix,
                "scopes": item.scopes_json or [],
                "is_active": item.is_active,
                "created_at": item.created_at.isoformat(),
                "last_used_at": item.last_used_at.isoformat() if item.last_used_at else None,
                "revoked_at": item.revoked_at.isoformat() if item.revoked_at else None,
            }
            for item in result.scalars().all()
        ]
    }


@router.post("")
async def create_api_key(
    req: APIKeyCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record, raw_key = await APIKeyService.create_key(db, current_user, req.name, req.scopes)
    await db.commit()
    return {
        "id": record.id,
        "name": record.name,
        "api_key": raw_key,
        "key_prefix": record.key_prefix,
        "scopes": record.scopes_json or [],
        "created_at": record.created_at.isoformat(),
    }


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await APIKeyService.revoke_key(db, current_user, key_id)
    await db.commit()
    return {"status": "revoked", "key_id": key_id}
