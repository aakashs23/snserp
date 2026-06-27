import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.models.document_permissions import DocumentPermission
from app.models.documents import Document
from app.models.users import User
from app.models.activity import ActivityLog
from app.schemas.document_permissions import DocumentPermissionCreate, DocumentPermissionUpdate, DocumentPermissionResponse

router = APIRouter()

async def log_activity(db: AsyncSession, user_id: uuid.UUID, action: str, entity_type: str, entity_id: uuid.UUID):
    log = ActivityLog(
        user_id=user_id,
        action=action[:100],
        entity_type=entity_type,
        entity_id=entity_id
    )
    db.add(log)

@router.get("/{document_id}/permissions", response_model=List[DocumentPermissionResponse])
async def list_permissions(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireRole(["admin"]))
):
    """List all explicit permissions for a document."""
    # Check document exists
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    stmt = select(DocumentPermission).options(selectinload(DocumentPermission.user)).where(DocumentPermission.document_id == document_id)
    result = await db.execute(stmt)
    return result.scalars().all()

@router.post("/{document_id}/permissions", response_model=DocumentPermissionResponse)
async def grant_permission(
    document_id: uuid.UUID,
    body: DocumentPermissionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireRole(["admin"]))
):
    """Grant document access to a user."""
    # Validate Document
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found or deleted")
        
    # Validate User
    target_user = await db.get(User, body.user_id)
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=404, detail="User not found or inactive")
        
    # Check if exists
    stmt = select(DocumentPermission).where(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == body.user_id
    )
    res = await db.execute(stmt)
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Permission already exists for this user")
        
    perm = DocumentPermission(
        id=uuid.uuid4(),
        document_id=document_id,
        user_id=body.user_id,
        can_view=body.can_view,
        can_download=body.can_download,
        can_edit=body.can_edit,
        granted_by=current_user.id
    )
    db.add(perm)
    
    await log_activity(db, current_user.id, f"GRANT_PERMISSION to {target_user.email}", "document", document_id)
    await db.commit()
    await db.refresh(perm, ["user"])
    return perm

@router.put("/{document_id}/permissions/{user_id}", response_model=DocumentPermissionResponse)
async def update_permission(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    body: DocumentPermissionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireRole(["admin"]))
):
    """Update existing document permissions."""
    stmt = select(DocumentPermission).options(selectinload(DocumentPermission.user)).where(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == user_id
    )
    res = await db.execute(stmt)
    perm = res.scalar_one_or_none()
    
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
        
    perm.can_view = body.can_view
    perm.can_download = body.can_download
    perm.can_edit = body.can_edit
    
    await log_activity(db, current_user.id, f"UPDATE_PERMISSION for {perm.user.email}", "document", document_id)
    await db.commit()
    await db.refresh(perm)
    return perm

@router.delete("/{document_id}/permissions/{user_id}")
async def revoke_permission(
    document_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireRole(["admin"]))
):
    """Revoke document permissions."""
    stmt = select(DocumentPermission).options(selectinload(DocumentPermission.user)).where(
        DocumentPermission.document_id == document_id,
        DocumentPermission.user_id == user_id
    )
    res = await db.execute(stmt)
    perm = res.scalar_one_or_none()
    
    if not perm:
        raise HTTPException(status_code=404, detail="Permission not found")
        
    email = perm.user.email
    await db.delete(perm)
    
    await log_activity(db, current_user.id, f"REVOKE_PERMISSION from {email}", "document", document_id)
    await db.commit()
    
    return {"message": "Permission revoked"}
