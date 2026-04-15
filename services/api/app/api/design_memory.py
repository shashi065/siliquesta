"""Design memory API endpoints - store and search designs."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User
from app.services.design_memory import DesignMemoryService, DesignMemoryRecord, SimilaritySearchResult, MemoryStats

router = APIRouter(prefix="/memory", tags=["design-memory"])
memory_service = DesignMemoryService()


# Request/Response Models
class StoreDesignRequest(BaseModel):
    """Request to store a design in memory."""

    inputs: dict = Field(..., description="Design inputs (wn, wp, vdd, temp, etc.)")
    outputs: dict | None = Field(None, description="Design outputs (freq, power, delay, etc.)")
    metadata: dict | None = Field(None, description="Additional metadata")
    title: str | None = Field(None, description="Human-readable design title")
    summary: str | None = Field(None, description="Brief description of design")
    source_scope: str = Field("user_submission", description="Origin of design")
    project_id: int | None = Field(None, description="Associated project ID")
    tags: list[str] | None = Field(None, description="User-defined tags")


class StoreDesignResponse(BaseModel):
    """Response from storing a design."""

    record_id: int
    title: str
    source_scope: str
    created_at: str
    similarity_score: float = 1.0


class SearchRequest(BaseModel):
    """Request to search for similar designs."""

    inputs: dict = Field(..., description="Query inputs to match")
    outputs: dict | None = Field(None, description="Query outputs (optional)")
    top_k: int = Field(5, ge=1, le=100, description="Number of results")
    min_similarity: float = Field(0.5, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: dict | None = Field(None, description="Optional filters (source_scope, tags, etc.)")


class SearchResponse(BaseModel):
    """Response from similarity search."""

    query_inputs: dict
    query_outputs: dict | None = None
    hits: list[dict]
    search_time_ms: float
    total_results: int


class MemoryStatsResponse(BaseModel):
    """Memory usage statistics."""

    total_designs: int
    total_inputs_stored: int
    total_outputs_stored: int
    average_similarity_score: float
    most_used_scope: str | None
    indexed_designs: int
    size_bytes: int


class DesignListResponse(BaseModel):
    """Response with list of designs."""

    designs: list[dict]
    total: int
    limit: int
    offset: int


class RecommendationRequest(BaseModel):
    """Request for design recommendations."""

    inputs: dict
    recommendation_type: str = Field("similar_designs", description="Type: similar_designs, best_performers")
    count: int = Field(5, ge=1, le=50, description="Number of recommendations")


class BatchSearchRequest(BaseModel):
    """Request to search multiple designs."""

    queries: list[dict] = Field(..., description="List of query dicts with 'inputs' and optional 'outputs'")
    top_k: int = Field(5, ge=1, le=50, description="Results per query")


# Endpoints


@router.post("/store", response_model=StoreDesignResponse)
async def store_design(
    req: StoreDesignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Store a design in memory with automatic FAISS indexing.

    The design is encoded into an 18-dimensional feature vector and indexed
    for fast similarity search. Returns immediately after storing.

    **Example:**
    ```json
    {
      "inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8, "temp": 27},
      "outputs": {"freq": 2.5, "power": 100, "delay": 0.4},
      "title": "Optimized design v1",
      "source_scope": "optimization",
      "tags": ["fast", "power-optimized"]
    }
    ```
    """
    try:
        record = await memory_service.store_design(
            db=db,
            user=current_user,
            inputs=req.inputs,
            outputs=req.outputs,
            metadata=req.metadata,
            title=req.title,
            summary=req.summary,
            source_scope=req.source_scope,
            project_id=req.project_id,
            tags=req.tags,
        )

        return StoreDesignResponse(
            record_id=record.record_id,
            title=record.title,
            source_scope=record.source_scope,
            created_at=record.created_at,
            similarity_score=record.similarity_score,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store design: {str(e)}")


@router.post("/search", response_model=SearchResponse)
async def search_similar(
    req: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for similar designs in memory using FAISS indexing.

    Returns ranked list of similar designs with similarity scores.
    Uses cosine similarity on 18-dimensional feature vectors.

    **Example:**
    ```json
    {
      "inputs": {"wn": 1.4, "wp": 2.1, "vdd": 1.8, "temp": 27},
      "top_k": 10,
      "min_similarity": 0.7,
      "filters": {"source_scope": "optimization"}
    }
    ```
    """
    try:
        result = await memory_service.search_similar(
            db=db,
            user=current_user,
            inputs=req.inputs,
            outputs=req.outputs,
            top_k=req.top_k,
            min_similarity=req.min_similarity,
            filters=req.filters,
        )

        return SearchResponse(
            query_inputs=result.query_inputs,
            query_outputs=result.query_outputs,
            hits=[hit.to_dict() for hit in result.hits],
            search_time_ms=result.search_time_ms,
            total_results=result.total_results,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/batch-search")
async def batch_search(
    req: BatchSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search for multiple designs in parallel.

    Efficient batch similarity search for multiple queries.

    **Example:**
    ```json
    {
      "queries": [
        {"inputs": {"wn": 1.5, "wp": 2.0, "vdd": 1.8}},
        {"inputs": {"wn": 1.2, "wp": 1.8, "vdd": 1.6}}
      ],
      "top_k": 5
    }
    ```
    """
    try:
        results = await memory_service.batch_search(
            db=db, user=current_user, queries=req.queries, top_k=req.top_k
        )

        return {
            "results": [
                {
                    "query_inputs": r.query_inputs,
                    "hits": [hit.to_dict() for hit in r.hits],
                    "search_time_ms": r.search_time_ms,
                    "total_results": r.total_results,
                }
                for r in results
            ],
            "batch_count": len(results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch search failed: {str(e)}")


@router.get("/stats", response_model=MemoryStatsResponse)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get statistics about user's design memory.

    Returns info about:
    - Total designs stored
    - Storage size and indexing status
    - Most commonly used design scope
    - Average design similarity

    **Typical Response:**
    ```json
    {
      "total_designs": 42,
      "total_inputs_stored": 42,
      "total_outputs_stored": 35,
      "average_similarity_score": 0.82,
      "most_used_scope": "optimization",
      "indexed_designs": 42,
      "size_bytes": 2097152
    }
    ```
    """
    try:
        stats = await memory_service.get_memory_stats(db=db, user=current_user)

        return MemoryStatsResponse(
            total_designs=stats.total_designs,
            total_inputs_stored=stats.total_inputs_stored,
            total_outputs_stored=stats.total_outputs_stored,
            average_similarity_score=stats.average_similarity_score,
            most_used_scope=stats.most_used_scope,
            indexed_designs=stats.indexed_designs,
            size_bytes=stats.size_bytes,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.post("/recommend", response_model=list[dict])
async def get_recommendations(
    req: RecommendationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get design recommendations based on input criteria.

    Supports multiple recommendation strategies:
    - `similar_designs`: Find designs similar to inputs
    - `best_performers`: Get highest-performing designs

    **Example:**
    ```json
    {
      "inputs": {"wn": 1.5, "wp": 2.0},
      "recommendation_type": "similar_designs",
      "count": 5
    }
    ```
    """
    try:
        records = await memory_service.find_recommendations(
            db=db,
            user=current_user,
            inputs=req.inputs,
            recommendation_type=req.recommendation_type,
            count=req.count,
        )

        return [r.to_dict() for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/list", response_model=DesignListResponse)
async def list_designs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", regex="^(created_at|title|source_scope)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all designs in memory with pagination.

    Supports sorting by created_at, title, or source_scope.

    **Example:**
    `/memory/list?limit=50&offset=0&sort_by=created_at&order=desc`
    """
    try:
        designs = await memory_service.list_designs(
            db=db,
            user=current_user,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order,
        )

        return DesignListResponse(
            designs=[d.to_dict() for d in designs],
            total=len(designs),
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list designs: {str(e)}")


@router.get("/{record_id}")
async def get_design(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a specific design from memory by ID.

    Returns full design details including inputs, outputs, and metadata.
    """
    try:
        design = await memory_service.get_design_by_id(db=db, user=current_user, record_id=record_id)

        if not design:
            raise HTTPException(status_code=404, detail="Design not found")

        return design.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get design: {str(e)}")


@router.delete("/{record_id}")
async def delete_design(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a design from memory.

    After deletion, memory indexes are automatically rebuilt.
    """
    try:
        success = await memory_service.delete_design(db=db, user=current_user, record_id=record_id)

        if not success:
            raise HTTPException(status_code=404, detail="Design not found")

        return {"status": "deleted", "record_id": record_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete design: {str(e)}")


@router.get("/export/json")
async def export_json(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all designs as JSON."""
    try:
        data = await memory_service.export_memory(db=db, user=current_user, format="json")
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.get("/export/csv")
async def export_csv(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Export all designs as CSV."""
    try:
        data = await memory_service.export_memory(db=db, user=current_user, format="csv")
        return {"csv": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")
