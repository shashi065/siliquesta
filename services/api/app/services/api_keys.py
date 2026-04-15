"""API key management for machine-to-machine access."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import APIKey, AuditEvent, User


class APIKeyService:
    @staticmethod
    def _hash_key(raw_key: str) -> str:
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _prefix(raw_key: str) -> str:
        return raw_key[: min(len(raw_key), 12)]

    @classmethod
    def generate_raw_key(cls) -> str:
        return f"{settings.API_KEY_PREFIX}{secrets.token_urlsafe(settings.API_KEY_BYTES)}"

    @classmethod
    async def create_key(
        cls,
        db: AsyncSession,
        user: User,
        name: str,
        scopes: list[str] | None = None,
    ) -> tuple[APIKey, str]:
        raw_key = cls.generate_raw_key()
        record = APIKey(
            user_id=user.id,
            name=name.strip(),
            key_prefix=cls._prefix(raw_key),
            key_hash=cls._hash_key(raw_key),
            scopes_json=scopes or ["api:*"],
        )
        db.add(record)
        db.add(
            AuditEvent(
                user_id=user.id,
                actor_key=f"user:{user.id}",
                action="api_key.created",
                scope="auth",
                details_json={"name": name, "scopes": scopes or ["api:*"]},
            )
        )
        await db.flush()
        return record, raw_key

    @classmethod
    async def resolve_user_from_key(cls, db: AsyncSession, raw_key: str | None) -> User | None:
        if not raw_key:
            return None
        hashed = cls._hash_key(raw_key.strip())
        result = await db.execute(select(APIKey).where(APIKey.key_hash == hashed, APIKey.is_active.is_(True)))
        record = result.scalar_one_or_none()
        if record is None:
            return None
        user_result = await db.execute(select(User).where(User.id == record.user_id, User.is_active.is_(True)))
        user = user_result.scalar_one_or_none()
        if user is None:
            return None
        record.last_used_at = datetime.utcnow()
        return user

    @classmethod
    async def revoke_key(cls, db: AsyncSession, user: User, key_id: int) -> None:
        result = await db.execute(select(APIKey).where(APIKey.id == key_id, APIKey.user_id == user.id))
        record = result.scalar_one_or_none()
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found.")
        record.is_active = False
        record.revoked_at = datetime.utcnow()
        db.add(
            AuditEvent(
                user_id=user.id,
                actor_key=f"user:{user.id}",
                action="api_key.revoked",
                scope="auth",
                details_json={"key_id": key_id, "name": record.name},
            )
        )
