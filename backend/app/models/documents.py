"""Document-related models: Document, DocumentMetadata, DocumentAI."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Table,
    Column,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin

# ── Association table (many-to-many: Document ↔ User for sharing) ────────────
document_shares = Table(
    "document_shares",
    Base.metadata,
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id",
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Document(UUIDPrimaryKeyMixin, Base):
    """Uploaded document record."""

    __tablename__ = "documents"

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_size: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ai_category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    upload_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="approved", server_default="approved"
    )

    # Relationships
    uploader = relationship(
        "User", foreign_keys=[uploaded_by], back_populates="documents"
    )
    metadata_info = relationship(
        "DocumentMetadata", back_populates="document", uselist=False, cascade="all, delete-orphan"
    )
    ai_info = relationship("DocumentAI", back_populates="document", uselist=False, cascade="all, delete-orphan")
    shared_with = relationship(
        "User",
        secondary=document_shares,
        backref="shared_documents"
    )


class DocumentMetadata(UUIDPrimaryKeyMixin, Base):
    """Extracted / user-supplied metadata for a document."""

    __tablename__ = "document_metadata"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True
    )
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    language: Mapped[str | None] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    invoice_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    customer_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    gst_number: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    document = relationship("Document", back_populates="metadata_info")


class DocumentAI(UUIDPrimaryKeyMixin, Base):
    """AI processing state and results for a document."""

    __tablename__ = "document_ai"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True
    )
    ocr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    embedding_status: Mapped[str] = mapped_column(
        String(30), default="pending", server_default="pending"
    )
    chromadb_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    document = relationship("Document", back_populates="ai_info")
