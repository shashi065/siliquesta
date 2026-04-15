"""Database connection and initialization."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# Async database setup
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.debug_enabled,
    future=True,
    pool_pre_ping=True,
    pool_size=settings.DATABASE_POOL_SIZE if not settings.DATABASE_URL.startswith("sqlite") else 1,
    max_overflow=settings.DATABASE_MAX_OVERFLOW if not settings.DATABASE_URL.startswith("sqlite") else 0,
    pool_timeout=settings.DATABASE_POOL_TIMEOUT if not settings.DATABASE_URL.startswith("sqlite") else 30,
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def init_db():
    """Initialize database tables"""
    try:
        import app.models  # noqa: F401
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database tables initialized")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        logger.warning("Continuing without persistent database initialization for this run")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for database session"""
    async with async_session() as session:
        yield session


async def database_healthcheck() -> dict:
    """Low-cost DB health probe for readiness checks."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "database_url": settings.DATABASE_URL.split("://", 1)[0]}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}
