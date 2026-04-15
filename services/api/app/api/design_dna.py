"""Design DNA storage and similarity search endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models import DesignDNARecord, User
from app.services.design_dna import DesignDNAService

router = APIRouter()
design_dna_service = DesignDNAService()


class DesignDNAIngestRequest(BaseModel):
    source_scope: str
    title: str
    summary: str | None = None
    project_id: int | None = None
    inputs: dict
    outputs: dict | None = None
    metadata: dict | None = None


class DesignDNASearchRequest(BaseModel):
    inputs: dict
    outputs: dict | None = None
    top_k: int = 5


@router.get("/mine")
async def list_design_dna(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DesignDNARecord)
        .where(DesignDNARecord.user_id == current_user.id)
        .order_by(DesignDNARecord.created_at.desc())
        .limit(min(max(limit, 1), 200))
    )
    return {
        "records": [
            {
                "id": item.id,
                "title": item.title,
                "source_scope": item.source_scope,
                "summary": item.summary,
                "created_at": item.created_at.isoformat(),
                "inputs": item.input_json,
                "outputs": item.output_json,
                "metadata": item.metadata_json,
            }
            for item in result.scalars().all()
        ]
    }


@router.post("/ingest")
async def ingest_design_dna(
    req: DesignDNAIngestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await design_dna_service.ingest(
        db=db,
        user=current_user,
        source_scope=req.source_scope,
        title=req.title,
        summary=req.summary,
        inputs=req.inputs,
        outputs=req.outputs,
        metadata=req.metadata,
        project_id=req.project_id,
    )
    await db.commit()
    return {
        "id": record.id,
        "title": record.title,
        "source_scope": record.source_scope,
        "created_at": record.created_at.isoformat(),
    }


@router.post("/search")
async def search_design_dna(
    req: DesignDNASearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hits = await design_dna_service.search(
        db=db,
        user=current_user,
        query_inputs=req.inputs,
        query_outputs=req.outputs,
        top_k=req.top_k,
    )
    return {"hits": [hit.__dict__ for hit in hits]}
