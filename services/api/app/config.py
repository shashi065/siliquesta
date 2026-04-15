"""Configuration management."""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings

ROOT_DIR = Path(__file__).resolve().parents[3]
DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{(ROOT_DIR / 'backend_storage' / 'siliquesta.db').as_posix()}"
DEFAULT_FAISS_PATH = str((ROOT_DIR / "services" / "api" / "data" / "faiss_index").resolve())


def _parse_bool(value: str | bool | None, default: bool = True) -> bool:
    """Tolerant boolean parsing for noisy machine-level environment variables."""
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().lower()
    if normalized in {"1", "true", "yes", "on", "debug", "dev"}:
        return True
    if normalized in {"0", "false", "no", "off", "release", "prod", "production"}:
        return False
    return default


def _normalize_database_url(url: str) -> str:
    """Convert generic DB URLs into async SQLAlchemy URLs."""
    if url.startswith("postgresql+asyncpg://") or url.startswith("sqlite+aiosqlite://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    return url


class Settings(BaseSettings):
    """Application settings"""

    # Database
    DATABASE_URL: str = _normalize_database_url(os.getenv(
        "DATABASE_URL",
        DEFAULT_SQLITE_URL,
    ))
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    DATABASE_POOL_TIMEOUT: int = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Ollama (Local LLM)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    
    # FAISS (Vector DB)
    FAISS_INDEX_PATH: str = os.getenv("FAISS_INDEX_PATH", DEFAULT_FAISS_PATH)
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", os.getenv("REDIS_URL", "redis://localhost:6379/1"))
    
    # Server
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: str = os.getenv("DEBUG", "true")
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Platform / security
    API_KEY_PREFIX: str = os.getenv("API_KEY_PREFIX", "sqk_")
    API_KEY_BYTES: int = int(os.getenv("API_KEY_BYTES", "24"))
    DEFAULT_CONFIDENCE_THRESHOLD: float = float(os.getenv("DEFAULT_CONFIDENCE_THRESHOLD", "0.8"))
    METRICS_ENABLED: str = os.getenv("METRICS_ENABLED", "true")

    # Billing
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    # Design DNA / ML registry
    MODEL_REGISTRY_PATH: str = os.getenv("MODEL_REGISTRY_PATH", str((ROOT_DIR / "ai-engine" / "artifacts").resolve()))
    DATASET_REGISTRY_PATH: str = os.getenv("DATASET_REGISTRY_PATH", str((ROOT_DIR / "ai-engine" / "datasets").resolve()))

    @property
    def debug_enabled(self) -> bool:
        return _parse_bool(self.DEBUG)

    @property
    def metrics_enabled(self) -> bool:
        return _parse_bool(self.METRICS_ENABLED)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
