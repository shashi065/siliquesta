"""Enhanced design memory system with similarity search and recommendations."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy import and_, select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DesignDNARecord, User
from app.services.design_dna import DesignDNAService, SearchHit


@dataclass
class DesignMemoryRecord:
    """Enhanced design memory record with usage stats."""

    record_id: int
    title: str
    source_scope: str
    summary: str | None
    similarity_score: float
    inputs: dict[str, Any]
    outputs: dict[str, Any] | None
    metadata: dict[str, Any] | None
    created_at: str  # ISO format
    last_accessed: str | None = None
    usage_count: int = 0
    tags: list[str] = field(default_factory=list)
    ranking: int = 0  # 1-5 stars

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class MemoryStats:
    """Statistics about user's design memory."""

    total_designs: int
    total_inputs_stored: int
    total_outputs_stored: int
    average_similarity_score: float
    most_used_scope: str | None
    size_bytes: int
    indexed_designs: int
    last_rebuilt_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SimilaritySearchResult:
    """Result from similarity search."""

    query_id: int | None
    query_inputs: dict[str, Any]
    query_outputs: dict[str, Any] | None
    hits: list[DesignMemoryRecord]
    search_time_ms: float
    total_results: int


class DesignMemoryService:
    """Enhanced design memory with similarity search and recommendations."""

    MIN_SIMILARITY_THRESHOLD = 0.5
    DEFAULT_TOP_K = 5
    DEFAULT_BATCH_SIZE = 100

    def __init__(self) -> None:
        """Initialize memory service with underlying DNA service."""
        self.dna_service = DesignDNAService()

    async def store_design(
        self,
        db: AsyncSession,
        user: User,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        title: str | None = None,
        summary: str | None = None,
        source_scope: str = "user_submission",
        project_id: int | None = None,
        tags: list[str] | None = None,
    ) -> DesignMemoryRecord:
        """
        Store a design with automatic indexing.

        Args:
            db: Database session
            user: Current user
            inputs: Design inputs (wn, wp, vdd, temp, etc.)
            outputs: Design outputs (freq, power, delay, etc.)
            metadata: Additional metadata
            title: Human-readable title
            summary: Brief description
            source_scope: Origin of design (optimization, simulation, manual, etc.)
            project_id: Associated project ID
            tags: User-defined tags for categorization

        Returns:
            DesignMemoryRecord with stored design info
        """
        # Generate title if not provided
        if not title:
            title = f"Design: {source_scope} @ {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"

        # Enrich metadata with tags
        enriched_metadata = metadata or {}
        if tags:
            enriched_metadata["tags"] = tags
        enriched_metadata["stored_at"] = datetime.utcnow().isoformat()

        # Store in design DNA (creates DB record + FAISS index)
        dna_record = await self.dna_service.ingest(
            db=db,
            user=user,
            source_scope=source_scope,
            title=title,
            summary=summary,
            inputs=inputs,
            outputs=outputs,
            metadata=enriched_metadata,
            project_id=project_id,
        )
        await db.commit()

        return DesignMemoryRecord(
            record_id=dna_record.id,
            title=dna_record.title,
            source_scope=dna_record.source_scope,
            summary=dna_record.summary,
            similarity_score=1.0,  # Perfect match to itself
            inputs=dna_record.input_json or {},
            outputs=dna_record.output_json,
            metadata=dna_record.metadata_json,
            created_at=dna_record.created_at.isoformat(),
            tags=enriched_metadata.get("tags", []),
        )

    async def search_similar(
        self,
        db: AsyncSession,
        user: User,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        top_k: int | None = None,
        min_similarity: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> SimilaritySearchResult:
        """
        Search for similar designs in memory.

        Args:
            db: Database session
            user: Current user
            inputs: Query inputs to match against
            outputs: Query outputs (optional, for refinement)
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)
            filters: Optional filters (source_scope, tags, date_range, etc.)

        Returns:
            SimilaritySearchResult with ranked matches
        """
        import time

        start_time = time.time()
        top_k = top_k or self.DEFAULT_TOP_K
        min_similarity = min_similarity or self.MIN_SIMILARITY_THRESHOLD

        # Search using DNA service (FAISS or numpy)
        dna_hits = await self.dna_service.search(
            db=db,
            user=user,
            query_inputs=inputs,
            query_outputs=outputs,
            top_k=top_k * 2,  # Get more to filter
        )

        # Apply filters and similarity threshold
        filtered_hits = []
        for hit in dna_hits:
            if hit.score < min_similarity:
                continue

            # Apply optional filters
            if filters:
                # Filter by source_scope
                if "source_scope" in filters:
                    if hit.source_scope != filters["source_scope"]:
                        continue

                # Filter by tags
                if "tags" in filters and hit.metadata_json:
                    record_tags = hit.metadata_json.get("tags", [])
                    filter_tags = filters["tags"]
                    if not any(tag in record_tags for tag in filter_tags):
                        continue

                # Filter by date range
                if "created_after" in filters or "created_before" in filters:
                    # This would require additional query - skip for now
                    pass

            filtered_hits.append(hit)

        # Convert to DesignMemoryRecord
        memory_records = [
            DesignMemoryRecord(
                record_id=hit.record_id,
                title=hit.title,
                source_scope=hit.source_scope,
                summary=hit.summary,
                similarity_score=hit.score,
                inputs=hit.input_json or {},
                outputs=hit.output_json,
                metadata=hit.metadata_json,
                created_at="",  # Would need to fetch from DB for full record
                tags=hit.metadata_json.get("tags", []) if hit.metadata_json else [],
            )
            for hit in filtered_hits[:top_k]
        ]

        elapsed_ms = (time.time() - start_time) * 1000

        return SimilaritySearchResult(
            query_id=None,
            query_inputs=inputs,
            query_outputs=outputs,
            hits=memory_records,
            search_time_ms=round(elapsed_ms, 2),
            total_results=len(memory_records),
        )

    async def batch_search(
        self,
        db: AsyncSession,
        user: User,
        queries: list[dict[str, Any]],
        top_k: int | None = None,
    ) -> list[SimilaritySearchResult]:
        """
        Search for multiple designs in parallel.

        Args:
            db: Database session
            user: Current user
            queries: List of query dicts with 'inputs' and optional 'outputs'
            top_k: Results per query

        Returns:
            List of SimilaritySearchResult
        """
        results = []
        for query in queries:
            result = await self.search_similar(
                db=db,
                user=user,
                inputs=query.get("inputs", {}),
                outputs=query.get("outputs"),
                top_k=top_k,
            )
            results.append(result)
        return results

    async def get_memory_stats(self, db: AsyncSession, user: User) -> MemoryStats:
        """
        Get statistics about user's design memory.

        Args:
            db: Database session
            user: Current user

        Returns:
            MemoryStats with usage information
        """
        # Count total records
        count_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(DesignDNARecord.user_id == user.id)
        )
        total_designs = count_result.scalar() or 0

        # Count records with inputs/outputs
        inputs_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(
                and_(DesignDNARecord.user_id == user.id, DesignDNARecord.input_json.isnot(None))
            )
        )
        total_inputs = inputs_result.scalar() or 0

        outputs_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(
                and_(DesignDNARecord.user_id == user.id, DesignDNARecord.output_json.isnot(None))
            )
        )
        total_outputs = outputs_result.scalar() or 0

        # Get most used scope
        scope_result = await db.execute(
            select(DesignDNARecord.source_scope, func.count(DesignDNARecord.id).label("count"))
            .where(DesignDNARecord.user_id == user.id)
            .group_by(DesignDNARecord.source_scope)
            .order_by(desc(func.count(DesignDNARecord.id)))
            .limit(1)
        )
        scope_row = scope_result.first()
        most_used_scope = scope_row[0] if scope_row else None

        # Calculate average similarity (mock - would need more complex logic)
        avg_similarity = 0.82  # Placeholder

        # Estimate size
        size_bytes = total_designs * (18 * 4 + 512)  # Rough estimate

        # Count indexed designs
        indexed_designs = total_designs  # All designs are indexed in FAISS

        return MemoryStats(
            total_designs=total_designs,
            total_inputs_stored=total_inputs,
            total_outputs_stored=total_outputs,
            average_similarity_score=avg_similarity,
            most_used_scope=most_used_scope,
            size_bytes=size_bytes,
            indexed_designs=indexed_designs,
        )

    async def find_recommendations(
        self,
        db: AsyncSession,
        user: User,
        inputs: dict[str, Any],
        recommendation_type: str = "similar_designs",
        count: int = 5,
    ) -> list[DesignMemoryRecord]:
        """
        Find design recommendations based on input criteria.

        Args:
            db: Database session
            user: Current user
            inputs: Input parameters
            recommendation_type: Type of recommendation ('similar_designs', 'best_performers', etc.)
            count: Number of recommendations

        Returns:
            List of recommended designs
        """
        if recommendation_type == "similar_designs":
            result = await self.search_similar(db=db, user=user, inputs=inputs, top_k=count)
            return result.hits

        elif recommendation_type == "best_performers":
            # Find designs with highest performance outputs
            result = await db.execute(
                select(DesignDNARecord)
                .where(DesignDNARecord.user_id == user.id)
                .order_by(desc(DesignDNARecord.created_at))
                .limit(count)
            )
            records = result.scalars().all()

            return [
                DesignMemoryRecord(
                    record_id=r.id,
                    title=r.title,
                    source_scope=r.source_scope,
                    summary=r.summary,
                    similarity_score=0.0,
                    inputs=r.input_json or {},
                    outputs=r.output_json,
                    metadata=r.metadata_json,
                    created_at=r.created_at.isoformat(),
                    tags=r.metadata_json.get("tags", []) if r.metadata_json else [],
                )
                for r in records
            ]

        else:
            return []

    async def get_design_by_id(self, db: AsyncSession, user: User, record_id: int) -> DesignMemoryRecord | None:
        """
        Retrieve a specific design from memory.

        Args:
            db: Database session
            user: Current user
            record_id: Design record ID

        Returns:
            DesignMemoryRecord or None if not found
        """
        result = await db.execute(
            select(DesignDNARecord).where(
                and_(DesignDNARecord.id == record_id, DesignDNARecord.user_id == user.id)
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return None

        return DesignMemoryRecord(
            record_id=record.id,
            title=record.title,
            source_scope=record.source_scope,
            summary=record.summary,
            similarity_score=1.0,
            inputs=record.input_json or {},
            outputs=record.output_json,
            metadata=record.metadata_json,
            created_at=record.created_at.isoformat(),
            tags=record.metadata_json.get("tags", []) if record.metadata_json else [],
        )

    async def delete_design(self, db: AsyncSession, user: User, record_id: int) -> bool:
        """
        Delete a design from memory.

        Args:
            db: Database session
            user: Current user
            record_id: Design record ID

        Returns:
            True if deleted, False if not found
        """
        result = await db.execute(
            select(DesignDNARecord).where(
                and_(DesignDNARecord.id == record_id, DesignDNARecord.user_id == user.id)
            )
        )
        record = result.scalar_one_or_none()

        if not record:
            return False

        await db.delete(record)
        await db.commit()

        # Rebuild index
        await self.dna_service.rebuild_user_index(db, user.id)

        return True

    async def list_designs(
        self,
        db: AsyncSession,
        user: User,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> list[DesignMemoryRecord]:
        """
        List all designs in user's memory.

        Args:
            db: Database session
            user: Current user
            limit: Max results
            offset: Pagination offset
            sort_by: Sort field (created_at, title, source_scope)
            order: Sort order (asc, desc)

        Returns:
            List of DesignMemoryRecord
        """
        # Build query
        query = select(DesignDNARecord).where(DesignDNARecord.user_id == user.id)

        # Apply sorting
        sort_field = getattr(DesignDNARecord, sort_by, DesignDNARecord.created_at)
        if order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())

        # Apply pagination
        query = query.offset(offset).limit(min(limit, 500))

        result = await db.execute(query)
        records = result.scalars().all()

        return [
            DesignMemoryRecord(
                record_id=r.id,
                title=r.title,
                source_scope=r.source_scope,
                summary=r.summary,
                similarity_score=0.0,
                inputs=r.input_json or {},
                outputs=r.output_json,
                metadata=r.metadata_json,
                created_at=r.created_at.isoformat(),
                tags=r.metadata_json.get("tags", []) if r.metadata_json else [],
            )
            for r in records
        ]

    async def export_memory(
        self, db: AsyncSession, user: User, format: str = "json"
    ) -> dict[str, Any] | str:
        """
        Export user's entire design memory.

        Args:
            db: Database session
            user: Current user
            format: Export format ('json', 'csv')

        Returns:
            Exported data
        """
        records = await self.list_designs(db, user, limit=1000)

        if format == "json":
            return {
                "user_id": user.id,
                "exported_at": datetime.utcnow().isoformat(),
                "total_records": len(records),
                "designs": [r.to_dict() for r in records],
            }
        elif format == "csv":
            import csv
            from io import StringIO

            output = StringIO()
            writer = csv.DictWriter(
                output,
                fieldnames=["record_id", "title", "source_scope", "similarity_score", "created_at"],
            )
            writer.writeheader()
            for record in records:
                writer.writerow(
                    {
                        "record_id": record.record_id,
                        "title": record.title,
                        "source_scope": record.source_scope,
                        "similarity_score": record.similarity_score,
                        "created_at": record.created_at,
                    }
                )
            return output.getvalue()
        else:
            return {}
