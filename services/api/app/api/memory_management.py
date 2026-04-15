"""Design memory management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.memory_manager import MemoryManager

router = APIRouter(prefix="/memory/manage", tags=["memory-management"])
manager = MemoryManager()


# Request/Response Models
class CleanupRequest(BaseModel):
    """Request to cleanup old records."""

    days_old: int = Field(90, ge=7, le=365, description="Remove records older than this many days")
    dry_run: bool = Field(True, description="If True, only report what would be deleted")


class ConsolidateRequest(BaseModel):
    """Request to consolidate similar designs."""

    similarity_threshold: float = Field(0.95, ge=0.5, le=1.0, description="Threshold for similarity")


class HealthReport(BaseModel):
    """Memory health report."""

    total_designs: int
    designs_with_outputs: int
    coverage: float
    oldest_design_days: int
    newest_design_days: int
    health_score: int
    recommendations: list[str]


class DuplicateGroup(BaseModel):
    """Group of similar/duplicate designs."""

    group: list[dict]
    similarity: float
    recommendation: str


class DistributionReport(BaseModel):
    """Memory distribution analysis."""

    total_records: int
    scope_distribution: dict[str, int]
    parameter_ranges: dict
    output_performance: dict
    with_outputs_count: int


# Endpoints


@router.get("/health", response_model=HealthReport)
async def get_memory_health(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get overall health of design memory.

    Analyzes:
    - Total designs stored
    - Data completeness (% with outputs)
    - Age of designs
    - Overall health score (0-100)

    **Returns:**
    - `health_score`: Overall rating (higher is better)
    - `recommendations`: Actionable improvement suggestions
    """
    try:
        health = await manager.get_memory_health(db=db, user=current_user)
        return HealthReport(**health)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get health report: {str(e)}")


@router.get("/analysis")
async def analyze_memory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get comprehensive analysis of design memory.

    Includes:
    - Health report
    - Distribution analysis
    - Duplicate detection
    - Parameter statistics

    **Returns comprehensive metrics for memory optimization.**
    """
    try:
        analysis = await manager.export_analysis(db=db, user=current_user)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/distribution", response_model=DistributionReport)
async def analyze_distribution(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Analyze distribution of designs across sources and parameters.

    Shows:
    - How designs are distributed by source_scope
    - Parameter ranges and statistics
    - Output performance distribution
    - Completeness metrics
    """
    try:
        dist = await manager.analyze_memory_distribution(db=db, user=current_user)
        return DistributionReport(**dist)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Distribution analysis failed: {str(e)}")


@router.get("/duplicates", response_model=list[DuplicateGroup])
async def find_duplicates(
    similarity_threshold: float = 0.95,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Find similar/duplicate designs in memory.

    Returns groups of designs that are very similar based on
    feature vector similarity. Useful for identifying redundancy.

    **Parameters:**
    - `similarity_threshold`: Only return groups with similarity ≥ this (default 0.95)

    **Use cases:**
    - Clean up redundant designs
    - Identify design patterns
    - Consolidate memory
    """
    try:
        duplicates = await manager.find_duplicates(
            db=db, user=current_user, similarity_threshold=similarity_threshold
        )
        return [DuplicateGroup(**d) for d in duplicates]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate detection failed: {str(e)}")


@router.post("/cleanup", response_model=dict)
async def cleanup_old_records(
    req: CleanupRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Remove designs older than specified duration.

    **Parameters:**
    - `days_old`: Only delete records older than this many days
    - `dry_run`: If True, only report what would be deleted (default: True)

    **Safety:**
    - Default is dry-run mode (no data deleted)
    - Explicitly set `dry_run=false` to actually delete
    - Recommended: Always run dry-run first to verify

    **Example:**
    ```json
    {
      "days_old": 90,
      "dry_run": true
    }
    ```
    """
    try:
        result = await manager.cleanup_old_records(
            db=db,
            user=current_user,
            days_old=req.days_old,
            dry_run=req.dry_run,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@router.post("/consolidate", response_model=dict)
async def consolidate_duplicates(
    req: ConsolidateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Consolidate similar designs by removing duplicates.

    **Parameters:**
    - `similarity_threshold`: Designs with similarity ≥ this are consolidated

    **Behavior:**
    - Identifies groups of similar designs
    - Keeps oldest/first record from each group
    - Deletes other similar records
    - Rebuilds indexes automatically

    **Warning:** This operation is permanent. Review duplicates first with `/duplicates` endpoint.

    **Example:**
    ```json
    {
      "similarity_threshold": 0.95
    }
    ```
    """
    try:
        result = await manager.consolidate_similar(
            db=db, user=current_user, similarity_threshold=req.similarity_threshold
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Consolidation failed: {str(e)}")


@router.post("/rebuild-indexes", response_model=dict)
async def rebuild_indexes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rebuild FAISS indexes for design memory.

    **When to use:**
    - After bulk imports
    - If search results seem degraded
    - Regular maintenance (monthly)

    **What happens:**
    - Reprocesses all designs
    - Rebuilds FAISS vector index
    - Optimizes search performance

    **Note:** This operation is safe and does not modify any designs.
    """
    try:
        result = await manager.rebuild_indexes(db=db, user=current_user)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")
