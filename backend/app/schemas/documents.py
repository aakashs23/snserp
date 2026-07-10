from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List

class DocumentMetadataResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    document_date: Optional[date] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    confidence_score: Optional[float] = None

class DocumentUpdate(BaseModel):
    # Bounds mirror the column widths in models/documents.py.
    original_name: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, max_length=50)

class DocumentAIResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary: Optional[str] = None
    embedding_status: str
    processed_at: Optional[datetime] = None

class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    file_name: str
    original_name: str
    display_name: Optional[str] = None
    storage_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    category: Optional[str] = None
    ai_category: Optional[str] = None
    uploaded_by: UUID
    upload_date: datetime
    version: int
    metadata_info: Optional[DocumentMetadataResponse] = None
    ai_info: Optional[DocumentAIResponse] = None


class DocumentCombinedResponse(BaseModel):
    """Combined document view with all AI and metadata in one response."""
    model_config = ConfigDict(from_attributes=True)
    
    # Document core fields
    id: UUID
    file_name: str
    original_name: str
    display_name: Optional[str] = None
    storage_path: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    category: Optional[str] = None
    uploaded_by: UUID
    upload_date: datetime
    version: int
    
    # AI category and status
    ai_category: Optional[str] = None
    ai_status: str = "pending"  # embedding_status renamed
    
    # Document state
    status: str = "approved"
    shared_with_ids: List[UUID] = Field(default_factory=list)
    
    # Metadata fields
    title: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List[str]] = None
    document_date: Optional[date] = None
    page_count: Optional[int] = None
    language: Optional[str] = None
    confidence_score: Optional[float] = None
    
    # AI processing fields
    summary: Optional[str] = None
    processed_at: Optional[datetime] = None
    
    @staticmethod
    def from_document(doc) -> "DocumentCombinedResponse":
        """Build combined response from Document model with related objects."""
        return DocumentCombinedResponse(
            # Document fields
            id=doc.id,
            file_name=doc.file_name,
            original_name=doc.original_name,
            display_name=doc.display_name,
            storage_path=doc.storage_path,
            file_size=doc.file_size,
            mime_type=doc.mime_type,
            category=doc.category,
            uploaded_by=doc.uploaded_by,
            upload_date=doc.upload_date,
            version=doc.version,
            # AI fields
            ai_category=doc.ai_category,
            ai_status=doc.ai_info.embedding_status if doc.ai_info else "pending",
            summary=doc.ai_info.summary if doc.ai_info else None,
            processed_at=doc.ai_info.processed_at if doc.ai_info else None,
            # Metadata fields
            title=doc.metadata_info.title if doc.metadata_info else None,
            description=doc.metadata_info.description if doc.metadata_info else None,
            keywords=doc.metadata_info.keywords if doc.metadata_info else None,
            document_date=doc.metadata_info.document_date if doc.metadata_info else None,
            page_count=doc.metadata_info.page_count if doc.metadata_info else None,
            language=doc.metadata_info.language if doc.metadata_info else None,
            confidence_score=doc.metadata_info.confidence_score if doc.metadata_info else None,
            status=getattr(doc, "status", "approved"),
            shared_with_ids=[u.id for u in getattr(doc, "shared_with", [])],
        )

class ShareRequest(BaseModel):
    user_ids: List[UUID]
