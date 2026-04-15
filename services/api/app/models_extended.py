"""Extended database models for production features."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ProjectVersion(Base):
    """Track project changes over time for versioning."""
    __tablename__ = "project_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3...
    design_state_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    change_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    change_type: Mapped[str] = mapped_column(String(32), nullable=False)  # create, update, simulate, optimize
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("project_id", "version_number", name="uq_project_version"),)


class SimulationResult(Base):
    """Store simulation results with caching."""
    __tablename__ = "simulation_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("compute_jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Input parameters
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    
    # Results
    gain: Mapped[float | None] = mapped_column(Float, nullable=True)
    delay: Mapped[float | None] = mapped_column(Float, nullable=True)
    power: Mapped[float | None] = mapped_column(Float, nullable=True)
    frequency: Mapped[float | None] = mapped_column(Float, nullable=True)
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Full results JSON
    results_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    # Quality metrics
    convergence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_estimate: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)  # queued, running, completed, failed
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AIOptimizationRun(Base):
    """Track AI optimization runs and results."""
    __tablename__ = "ai_optimization_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    job_id: Mapped[int | None] = mapped_column(ForeignKey("compute_jobs.id", ondelete="SET NULL"), nullable=True)
    
    # Baseline metrics
    baseline_params_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    baseline_gain: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_delay: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_power: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Optimization objectives
    objectives_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)  # weights for freq, power, health, cost
    
    # Optimized results
    optimized_params_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    optimized_gain: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimized_delay: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimized_power: Mapped[float | None] = mapped_column(Float, nullable=True)
    improvement_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Optimization process info
    iterations_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pareto_solutions_json: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    convergence_info_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    execution_time_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class CacheEntry(Base):
    """Simple in-memory cache with TTL."""
    __tablename__ = "cache_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    cache_value_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    ttl_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
