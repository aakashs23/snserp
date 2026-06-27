import sys

code = """
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
"""

path = "/Users/aakash/Documents/Projects/snserp/snserp/backend/app/api/documents.py"
with open(path, "a") as f:
    f.write(code)
