"""Persistent vector-based design memory with optional FAISS acceleration."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import DesignDNARecord, User

try:
    import faiss  # type: ignore
except Exception:  # pragma: no cover - optional runtime dependency
    faiss = None


@dataclass
class SearchHit:
    record_id: int
    score: float
    title: str
    source_scope: str
    summary: str | None
    input_json: dict[str, Any] | None
    output_json: dict[str, Any] | None
    metadata_json: dict[str, Any] | None


class DesignDNAService:
    VECTOR_SIZE = 18

    def __init__(self, index_root: str | None = None) -> None:
        self.index_root = Path(index_root or settings.FAISS_INDEX_PATH)
        self.index_root.mkdir(parents=True, exist_ok=True)

    @classmethod
    def encode_design(
        cls,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[float]:
        outputs = outputs or {}
        metadata = metadata or {}
        corner_map = {"SS": 0.0, "TT": 0.2, "FF": 0.4, "SF": 0.6, "FS": 0.8, "MC": 1.0}
        tech = float(inputs.get("tech_node", metadata.get("tech_node", 28.0)) or 28.0)
        corner = str(inputs.get("corner", metadata.get("corner", "TT"))).upper()
        vector = np.array(
            [
                float(inputs.get("wn", 0.0)),
                float(inputs.get("wp", 0.0)),
                float(inputs.get("vdd", 0.0)),
                float(inputs.get("temp", 27.0)),
                float(inputs.get("cl_ff", 0.0)),
                tech,
                corner_map.get(corner, 0.2),
                float(outputs.get("freq", outputs.get("freq_ghz", 0.0))),
                float(outputs.get("power", outputs.get("power_mw", 0.0))),
                float(outputs.get("delay", outputs.get("delay_ps", 0.0))),
                float(outputs.get("fom", 0.0)),
                float(outputs.get("health_score", 0.0)),
                float(outputs.get("confidence", 0.0)),
                float(metadata.get("reliability_score", 0.0)),
                float(metadata.get("estimated_error_percent", 0.0)),
                float(inputs.get("wp", 0.0)) / max(float(inputs.get("wn", 0.1)), 0.1),
                float(inputs.get("wn", 0.0)) + float(inputs.get("wp", 0.0)),
                1.0 / max(tech, 0.3),
            ],
            dtype=np.float32,
        )
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def _index_path(self, user_id: int) -> Path:
        return self.index_root / f"user_{user_id}_design_dna.index"

    def _meta_path(self, user_id: int) -> Path:
        return self.index_root / f"user_{user_id}_design_dna_meta.json"

    def _load_meta(self, user_id: int) -> list[int]:
        path = self._meta_path(user_id)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def _save_meta(self, user_id: int, ids: list[int]) -> None:
        self._meta_path(user_id).write_text(json.dumps(ids), encoding="utf-8")

    async def ingest(
        self,
        db: AsyncSession,
        user: User,
        source_scope: str,
        title: str,
        inputs: dict[str, Any],
        outputs: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        project_id: int | None = None,
        summary: str | None = None,
    ) -> DesignDNARecord:
        vector = self.encode_design(inputs, outputs, metadata)
        record = DesignDNARecord(
            user_id=user.id,
            project_id=project_id,
            source_scope=source_scope,
            title=title,
            summary=summary,
            feature_vector_json=vector,
            input_json=inputs,
            output_json=outputs,
            metadata_json=metadata,
        )
        db.add(record)
        await db.flush()
        await self.rebuild_user_index(db, user.id)
        return record

    async def rebuild_user_index(self, db: AsyncSession, user_id: int) -> None:
        result = await db.execute(
            select(DesignDNARecord)
            .where(DesignDNARecord.user_id == user_id)
            .order_by(DesignDNARecord.created_at.asc(), DesignDNARecord.id.asc())
        )
        records = result.scalars().all()
        ids = [record.id for record in records]
        self._save_meta(user_id, ids)
        vectors = np.array([record.feature_vector_json for record in records], dtype=np.float32) if records else np.zeros((0, self.VECTOR_SIZE), dtype=np.float32)

        if faiss is not None:
            index = faiss.IndexFlatIP(self.VECTOR_SIZE)
            if len(vectors):
                index.add(vectors)
            faiss.write_index(index, str(self._index_path(user_id)))
        else:
            np.save(self._index_path(user_id).with_suffix(".npy"), vectors)

    async def search(
        self,
        db: AsyncSession,
        user: User,
        query_inputs: dict[str, Any],
        query_outputs: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[SearchHit]:
        query_vec = np.array([self.encode_design(query_inputs, query_outputs)], dtype=np.float32)
        ids = self._load_meta(user.id)
        if not ids:
            return []
        result = await db.execute(
            select(DesignDNARecord).where(DesignDNARecord.user_id == user.id, DesignDNARecord.id.in_(ids))
        )
        records_by_id = {record.id: record for record in result.scalars().all()}

        scored_ids: list[tuple[int, float]] = []
        faiss_path = self._index_path(user.id)
        if faiss is not None and faiss_path.exists():
            index = faiss.read_index(str(faiss_path))
            scores, positions = index.search(query_vec, min(top_k, len(ids)))
            for pos, score in zip(positions[0], scores[0]):
                if pos >= 0 and pos < len(ids):
                    scored_ids.append((ids[pos], float(score)))
        else:
            matrix_path = faiss_path.with_suffix(".npy")
            if matrix_path.exists():
                vectors = np.load(matrix_path)
                sims = vectors @ query_vec[0]
                positions = np.argsort(-sims)[: min(top_k, len(ids))]
                scored_ids.extend((ids[int(pos)], float(sims[int(pos)])) for pos in positions)

        hits: list[SearchHit] = []
        for record_id, score in scored_ids:
            record = records_by_id.get(record_id)
            if record is None:
                continue
            hits.append(
                SearchHit(
                    record_id=record.id,
                    score=round(score, 5),
                    title=record.title,
                    source_scope=record.source_scope,
                    summary=record.summary,
                    input_json=record.input_json,
                    output_json=record.output_json,
                    metadata_json=record.metadata_json,
                )
            )
        return hits
