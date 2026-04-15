"""Project management and CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from app.api.auth import get_current_user
from app.database import get_db
from app.models import User, Project

router = APIRouter(prefix="/projects", tags=["Projects"])


# ============ Pydantic Models ============


class ProjectCreate(BaseModel):
    """Create a new project"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)


class ProjectUpdate(BaseModel):
    """Update an existing project"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = Field(None, max_items=10)
    design_state: Optional[dict] = Field(None)


class ProjectResponse(BaseModel):
    """Project response model"""
    id: int
    slug: str
    name: str
    description: Optional[str]
    design_state: Optional[dict]
    tags: Optional[List[str]]
    created_at: str
    updated_at: str


# ============ Endpoints ============


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    req: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new project"""
    # Generate slug from name
    slug = req.name.lower().replace(" ", "-").replace("/", "-")[:128]
    
    # Check if slug already exists for this user
    existing = await db.execute(
        select(Project).where(
            Project.user_id == current_user.id,
            Project.slug == slug
        )
    )
    
    if existing.scalar_one_or_none() is not None:
        # Add timestamp to make slug unique
        slug = f"{slug}-{int(datetime.utcnow().timestamp())}"
    
    project = Project(
        user_id=current_user.id,
        slug=slug,
        name=req.name,
        description=req.description,
        tags_json=req.tags or [],
        design_state_json={},
    )
    
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        design_state=project.design_state_json,
        tags=project.tags_json,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all projects for current user"""
    result = await db.execute(
        select(Project)
        .where(Project.user_id == current_user.id)
        .order_by(Project.updated_at.desc())
    )
    
    projects = result.scalars().all()
    return [
        ProjectResponse(
            id=p.id,
            slug=p.slug,
            name=p.name,
            description=p.description,
            design_state=p.design_state_json,
            tags=p.tags_json,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific project"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return ProjectResponse(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        design_state=project.design_state_json,
        tags=project.tags_json,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    req: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a project"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields
    if req.name is not None:
        project.name = req.name
    if req.description is not None:
        project.description = req.description
    if req.tags is not None:
        project.tags_json = req.tags
    if req.design_state is not None:
        project.design_state_json = req.design_state
    
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        slug=project.slug,
        name=project.name,
        description=project.description,
        design_state=project.design_state_json,
        tags=project.tags_json,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a project"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    await db.commit()


@router.post("/{project_id}/save-design")
async def save_design(
    project_id: int,
    design_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save design state for a project"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    project.design_state_json = design_data
    await db.commit()
    await db.refresh(project)
    
    return {
        "success": True,
        "design_state": project.design_state_json,
        "updated_at": project.updated_at.isoformat(),
    }


@router.get("/{project_id}/design-state")
async def get_design_state(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get design state for a project"""
    result = await db.execute(
        select(Project).where(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
    )
    
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return {
        "design_state": project.design_state_json or {},
        "updated_at": project.updated_at.isoformat(),
    }
