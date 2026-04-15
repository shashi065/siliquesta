"""Project sharing and collaboration API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Project, ProjectShare
from app.auth import get_current_user

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


class ShareRequest:
    """Request model for sharing projects"""
    def __init__(self, collaborator_email: str, role: str = "viewer"):
        self.collaborator_email = collaborator_email
        self.role = role


@router.post("/{project_id}/share")
async def share_project(
    project_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Share a project with another user"""
    # Verify ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find collaborator by email
    collaborator = db.query(User).filter(User.email == request.get("collaborator_email")).first()
    if not collaborator:
        raise HTTPException(status_code=404, detail="User not found")
    
    if collaborator.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot share with yourself")
    
    # Check if already shared
    existing_share = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id,
        ProjectShare.collaborator_id == collaborator.id
    ).first()
    
    if existing_share:
        raise HTTPException(status_code=400, detail="Project already shared with this user")
    
    # Create share record
    role = request.get("role", "viewer")
    share = ProjectShare(
        project_id=project_id,
        collaborator_id=collaborator.id,
        role=role,
        can_edit=role in ["editor", "admin"],
        can_run_simulations=role in ["editor", "admin"],
        can_share=role == "admin"
    )
    
    db.add(share)
    db.commit()
    db.refresh(share)
    
    return {
        "id": share.id,
        "project_id": project_id,
        "collaborator": {"id": collaborator.id, "email": collaborator.email, "name": collaborator.name},
        "role": role,
        "permissions": {
            "can_edit": share.can_edit,
            "can_run_simulations": share.can_run_simulations,
            "can_share": share.can_share
        }
    }


@router.get("/{project_id}/shares")
async def list_shares(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all collaborators on a project"""
    # Verify ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    shares = db.query(ProjectShare).filter(ProjectShare.project_id == project_id).all()
    
    result = []
    for share in shares:
        collaborator = db.query(User).filter(User.id == share.collaborator_id).first()
        result.append({
            "id": share.id,
            "collaborator": {
                "id": collaborator.id,
                "email": collaborator.email,
                "name": collaborator.name
            },
            "role": share.role,
            "permissions": {
                "can_edit": share.can_edit,
                "can_run_simulations": share.can_run_simulations,
                "can_share": share.can_share
            },
            "created_at": share.created_at.isoformat()
        })
    
    return result


@router.put("/{project_id}/shares/{share_id}")
async def update_share(
    project_id: int,
    share_id: int,
    request: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a project share (change role/permissions)"""
    # Verify ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    share = db.query(ProjectShare).filter(
        ProjectShare.id == share_id,
        ProjectShare.project_id == project_id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    # Update role
    new_role = request.get("role", share.role)
    share.role = new_role
    share.can_edit = new_role in ["editor", "admin"]
    share.can_run_simulations = new_role in ["editor", "admin"]
    share.can_share = new_role == "admin"
    
    db.commit()
    db.refresh(share)
    
    return {
        "id": share.id,
        "role": share.role,
        "permissions": {
            "can_edit": share.can_edit,
            "can_run_simulations": share.can_run_simulations,
            "can_share": share.can_share
        }
    }


@router.delete("/{project_id}/shares/{share_id}")
async def revoke_share(
    project_id: int,
    share_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Revoke access to a shared project"""
    # Verify ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.user_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    share = db.query(ProjectShare).filter(
        ProjectShare.id == share_id,
        ProjectShare.project_id == project_id
    ).first()
    
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    db.delete(share)
    db.commit()
    
    return {"status": "ok", "message": "Access revoked"}


@router.get("/shared")
async def list_shared_projects(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all projects shared with the current user"""
    shares = db.query(ProjectShare).filter(
        ProjectShare.collaborator_id == current_user.id
    ).all()
    
    result = []
    for share in shares:
        project = db.query(Project).filter(Project.id == share.project_id).first()
        owner = db.query(User).filter(User.id == project.user_id).first()
        
        result.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "owner": {
                "id": owner.id,
                "email": owner.email,
                "name": owner.name
            },
            "role": share.role,
            "permissions": {
                "can_edit": share.can_edit,
                "can_run_simulations": share.can_run_simulations,
                "can_share": share.can_share
            },
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        })
    
    return result
