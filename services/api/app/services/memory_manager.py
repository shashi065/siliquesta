"""Memory management utilities for design memory system."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

import numpy as np
from sqlalchemy import and_, select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import DesignDNARecord, User
from app.services.design_dna import DesignDNAService


class MemoryManager:
    """Utilities for managing design memory system."""

    def __init__(self) -> None:
        """Initialize memory manager."""
        self.dna_service = DesignDNAService()

    async def cleanup_old_records(
        self,
        db: AsyncSession,
        user: User,
        days_old: int = 90,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        """
        Remove designs older than specified days.

        Args:
            db: Database session
            user: User to cleanup for
            days_old: Remove records older than this many days
            dry_run: If True, only count records to delete (don't delete)

        Returns:
            Dict with cleanup stats
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)

        # Count old records
        count_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(
                and_(
                    DesignDNARecord.user_id == user.id,
                    DesignDNARecord.created_at < cutoff_date,
                )
            )
        )
        count = count_result.scalar() or 0

        if dry_run or count == 0:
            return {
                "dry_run": dry_run,
                "records_to_delete": count,
                "cutoff_date": cutoff_date.isoformat(),
                "deleted": False,
            }

        # Delete old records
        await db.execute(
            delete(DesignDNARecord).where(
                and_(
                    DesignDNARecord.user_id == user.id,
                    DesignDNARecord.created_at < cutoff_date,
                )
            )
        )
        await db.commit()

        # Rebuild index
        await self.dna_service.rebuild_user_index(db, user.id)

        return {
            "dry_run": False,
            "records_deleted": count,
            "cutoff_date": cutoff_date.isoformat(),
            "deleted": True,
        }

    async def find_duplicates(
        self,
        db: AsyncSession,
        user: User,
        similarity_threshold: float = 0.95,
    ) -> list[dict[str, Any]]:
        """
        Find similar/duplicate designs in user's memory.

        Args:
            db: Database session
            user: User to analyze
            similarity_threshold: Threshold for considering designs similar

        Returns:
            List of duplicate groups with similarity info
        """
        # Get all user records
        result = await db.execute(
            select(DesignDNARecord).where(DesignDNARecord.user_id == user.id)
        )
        records = result.scalars().all()

        if len(records) < 2:
            return []

        # Build vectors
        vectors = np.array([r.feature_vector_json for r in records], dtype=np.float32)

        # Compute similarity matrix
        similarities = vectors @ vectors.T

        # Find duplicates
        duplicates = []
        seen = set()

        for i in range(len(records)):
            if i in seen:
                continue

            group = [i]
            for j in range(i + 1, len(records)):
                if similarities[i, j] >= similarity_threshold:
                    group.append(j)
                    seen.add(j)

            if len(group) > 1:
                duplicates.append(
                    {
                        "group": [
                            {
                                "id": records[idx].id,
                                "title": records[idx].title,
                                "created_at": records[idx].created_at.isoformat(),
                            }
                            for idx in group
                        ],
                        "similarity": float(np.mean([similarities[group[0], idx] for idx in group[1:]])),
                        "recommendation": f"Consider consolidating these {len(group)} similar designs",
                    }
                )

        return duplicates

    async def analyze_memory_distribution(
        self,
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        """
        Analyze distribution of designs across sources and parameters.

        Args:
            db: Database session
            user: User to analyze

        Returns:
            Distribution stats
        """
        # Get all records
        result = await db.execute(
            select(DesignDNARecord).where(DesignDNARecord.user_id == user.id)
        )
        records = result.scalars().all()

        if not records:
            return {
                "total_records": 0,
                "distribution": {},
                "parameter_ranges": {},
            }

        # Distribution by source_scope
        scope_counts = {}
        for r in records:
            scope_counts[r.source_scope] = scope_counts.get(r.source_scope, 0) + 1

        # Parameter ranges
        param_ranges = {}
        all_inputs = [r.input_json or {} for r in records]

        for key in ["wn", "wp", "vdd", "temp", "cl_ff"]:
            values = [float(inp.get(key, 0)) for inp in all_inputs if key in inp]
            if values:
                param_ranges[key] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": np.mean(values),
                    "std": float(np.std(values)),
                }

        # Output performance distribution
        all_outputs = [r.output_json or {} for r in records]
        output_stats = {}

        for key in ["freq", "power", "delay"]:
            values = [float(out.get(key, 0)) for out in all_outputs if key in out]
            if values:
                output_stats[key] = {
                    "min": min(values),
                    "max": max(values),
                    "mean": np.mean(values),
                    "median": float(np.median(values)),
                }

        return {
            "total_records": len(records),
            "scope_distribution": scope_counts,
            "parameter_ranges": param_ranges,
            "output_performance": output_stats,
            "with_outputs_count": len([r for r in records if r.output_json]),
        }

    async def get_memory_health(
        self,
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        """
        Get overall health of design memory system.

        Args:
            db: Database session
            user: User to analyze

        Returns:
            Health report
        """
        # Count total
        count_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(DesignDNARecord.user_id == user.id)
        )
        total = count_result.scalar() or 0

        # Count with outputs
        outputs_result = await db.execute(
            select(func.count(DesignDNARecord.id)).where(
                and_(
                    DesignDNARecord.user_id == user.id,
                    DesignDNARecord.output_json.isnot(None),
                )
            )
        )
        with_outputs = outputs_result.scalar() or 0

        # Age stats
        age_result = await db.execute(
            select(func.min(DesignDNARecord.created_at), func.max(DesignDNARecord.created_at)).where(
                DesignDNARecord.user_id == user.id
            )
        )
        min_date, max_date = age_result.one()

        oldest_days = (datetime.utcnow() - min_date).days if min_date else 0
        newest_days = (datetime.utcnow() - max_date).days if max_date else 0

        # Calculate health score
        health_score = 100
        if total == 0:
            health_score = 0
        elif with_outputs / total < 0.7:
            health_score -= 10
        if oldest_days > 180:
            health_score -= 5

        return {
            "total_designs": total,
            "designs_with_outputs": with_outputs,
            "coverage": round((with_outputs / total * 100) if total > 0 else 0, 1),
            "oldest_design_days": oldest_days,
            "newest_design_days": newest_days,
            "health_score": max(0, health_score),
            "recommendations": _get_health_recommendations(total, with_outputs, oldest_days),
        }

    async def consolidate_similar(
        self,
        db: AsyncSession,
        user: User,
        similarity_threshold: float = 0.95,
        keep_best: bool = True,
    ) -> dict[str, Any]:
        """
        Consolidate similar designs by removing duplicates.

        Args:
            db: Database session
            user: User to consolidate for
            similarity_threshold: Threshold for similarity
            keep_best: If True, keep record with best performance

        Returns:
            Consolidation stats
        """
        duplicates = await self.find_duplicates(db, user, similarity_threshold)

        consolidated = 0
        for group in duplicates:
            if len(group["group"]) < 2:
                continue

            # Sort by ID (oldest first) or by performance if available
            ids_to_keep = sorted([g["id"] for g in group["group"]])
            keep_id = ids_to_keep[0]

            # Delete others
            for delete_id in ids_to_keep[1:]:
                await db.execute(
                    delete(DesignDNARecord).where(DesignDNARecord.id == delete_id)
                )
                consolidated += 1

        await db.commit()

        # Rebuild index
        if consolidated > 0:
            await self.dna_service.rebuild_user_index(db, user.id)

        return {
            "duplicate_groups_found": len(duplicates),
            "designs_consolidated": consolidated,
            "designs_remaining": (
                (await db.execute(
                    select(func.count(DesignDNARecord.id)).where(DesignDNARecord.user_id == user.id)
                )).scalar()
                or 0
            ),
        }

    async def rebuild_indexes(
        self,
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        """
        Rebuild FAISS indexes for user's memory.

        Args:
            db: Database session
            user: User to rebuild indexes for

        Returns:
            Rebuild stats
        """
        # Get all records
        result = await db.execute(
            select(DesignDNARecord).where(DesignDNARecord.user_id == user.id)
        )
        records = result.scalars().all()

        # Rebuild
        await self.dna_service.rebuild_user_index(db, user.id)

        return {
            "status": "rebuilt",
            "total_records": len(records),
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def export_analysis(
        self,
        db: AsyncSession,
        user: User,
    ) -> dict[str, Any]:
        """
        Export comprehensive analysis of user's design memory.

        Args:
            db: Database session
            user: User to analyze

        Returns:
            Comprehensive analysis report
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.id,
            "health": await self.get_memory_health(db, user),
            "distribution": await self.analyze_memory_distribution(db, user),
            "duplicates": await self.find_duplicates(db, user, 0.9),
        }


def _get_health_recommendations(total: int, with_outputs: int, oldest_days: int) -> list[str]:
    """Generate recommendations based on memory health."""
    recommendations = []

    if total == 0:
        recommendations.append("Start by storing some designs to build your memory.")
    elif total < 10:
        recommendations.append("Store more designs to improve recommendation quality.")

    if with_outputs / max(total, 1) < 0.7:
        recommendations.append("Many designs lack outputs. Consider running simulations to complete records.")

    if oldest_days > 180:
        recommendations.append("Some designs are very old. Consider reviewing and consolidating old records.")

    if not recommendations:
        recommendations.append("Your design memory is in excellent health!")

    return recommendations
