import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.models.documents import Document, DocumentAI
from app.models.users import User
from app.models.document_permissions import DocumentPermission
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.schemas.documents import DocumentResponse, DocumentCombinedResponse, ShareRequest
from app.config.supabase import supabase
from app.services.ai_pipeline import process_document_background
from app.services.activity_service import log_activity

router = APIRouter()

@router.post("/upload", response_model=DocumentCombinedResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    # 1. Read file bytes
    file_bytes = await file.read()
    
    # 2. Upload to Supabase Storage
    file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
    safe_filename = f"{uuid.uuid4()}.{file_extension}"
    storage_path = f"{current_user.id}/{safe_filename}"
    
    try:
        supabase.storage.from_("documents").upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": file.content_type}
        )
    except Exception as e:
        # Supabase Python client might raise exception if bucket doesn't exist
        raise HTTPException(status_code=500, detail=f"Storage upload failed: {str(e)}")

    # 3. Create Document DB record
    doc_id = uuid.uuid4()
    new_doc = Document(
        id=doc_id,
        file_name=safe_filename,
        original_name=file.filename,
        storage_path=storage_path,
        file_size=len(file_bytes),
        mime_type=file.content_type,
        uploaded_by=current_user.id
    )
    db.add(new_doc)
    
    # Create initial DocumentAI record
    doc_ai = DocumentAI(
        id=uuid.uuid4(),
        document_id=doc_id,
        embedding_status="pending"
    )
    db.add(doc_ai)
    
    await db.commit()
    await db.refresh(new_doc)
    
    # 4. Trigger AI Pipeline
    background_tasks.add_task(
        process_document_background,
        document_id=doc_id,
        file_bytes=file_bytes,
        file_name=file.filename,
        mime_type=file.content_type
    )
    
    # Eager load relationships for response
    result = await db.execute(
        select(Document)
        .options(
            selectinload(Document.metadata_info),
            selectinload(Document.ai_info),
            selectinload(Document.shared_with),
        )
        .where(Document.id == doc_id)
    )
    doc = result.scalar_one()
    await log_activity(db=db, user_id=current_user.id, action="Upload", module="Documents", object_affected=f"Document ID: {doc_id}")
    await db.commit()
    return DocumentCombinedResponse.from_document(doc)

@router.get("/", response_model=List[DocumentCombinedResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List documents with combined AI and metadata in a single response.
    Joins documents, document_ai, and document_metadata tables.
    Returns all needed fields for the Documents page in one API call.
    """
    query = select(Document).options(
        selectinload(Document.metadata_info),
        selectinload(Document.ai_info),
        selectinload(Document.shared_with),
    ).where(Document.is_deleted == False)

    if current_user.role.name in ["viewer", "accountant"]:
        query = query.join(DocumentPermission, Document.id == DocumentPermission.document_id).where(
            DocumentPermission.user_id == current_user.id,
            DocumentPermission.can_view == True,
            Document.status == "approved"
        )
    
    if search:
        query = query.where(Document.original_name.ilike(f"%{search}%"))
        
    query = query.order_by(desc(Document.upload_date)).offset(skip).limit(limit)
    result = await db.execute(query)
    documents = result.scalars().all()
    
    # Convert each document to combined response format
    return [DocumentCombinedResponse.from_document(doc) for doc in documents]

@router.get("/{document_id}/preview")
async def preview_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role.name in ["viewer", "accountant"]:
        if doc.status != "approved":
            raise HTTPException(status_code=403, detail="Access denied")
            
        stmt = select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == current_user.id,
            DocumentPermission.can_view == True
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You do not have permission to access this document.")
        
    try:
        res = supabase.storage.from_("documents").create_signed_url(doc.storage_path, 3600)
        return {"url": res.get("signedURL")}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate preview URL")

@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")
        
    if current_user.role.name in ["viewer", "accountant"]:
        if doc.status != "approved":
            raise HTTPException(status_code=403, detail="Access denied")
            
        stmt = select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == current_user.id,
            DocumentPermission.can_download == True
        )
        res = await db.execute(stmt)
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="You do not have permission to download this document.")
        
    try:
        res = supabase.storage.from_("documents").create_signed_url(doc.storage_path, 3600, options={"download": doc.original_name})
        return {"url": res.get("signedURL")}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to generate download URL")

@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc.is_deleted = True
    doc.deleted_at = func.now()
    await db.commit()
    return {"deleted": True}


@router.get("/trash/list", response_model=List[DocumentCombinedResponse])
async def list_trash(
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    query = select(Document).options(
        selectinload(Document.metadata_info),
        selectinload(Document.ai_info),
        selectinload(Document.shared_with),
    ).where(Document.is_deleted == True).order_by(desc(Document.deleted_at))
    
    result = await db.execute(query)
    documents = result.scalars().all()
    
    return [DocumentCombinedResponse.from_document(doc) for doc in documents]

@router.post("/{document_id}/restore")
async def restore_document(
    document_id: uuid.UUID,
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    if not doc or not doc.is_deleted:
        raise HTTPException(status_code=404, detail="Deleted document not found")
        
    doc.is_deleted = False
    doc.deleted_at = None
    await db.commit()
    return {"restored": True}

@router.delete("/{document_id}/permanent")
async def permanent_delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    doc = await db.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Delete from Supabase Storage
    try:
        supabase.storage.from_("documents").remove([doc.storage_path])
    except Exception as e:
        print(f"Failed to delete from storage: {e}")
        
    # Delete from DB
    await db.delete(doc)
    await db.commit()
    return {"permanently_deleted": True}
