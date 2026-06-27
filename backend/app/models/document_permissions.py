"""Document Permissions Model"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin, TimestampMixin

class DocumentPermission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Document-level permissions for individual users."""

    __tablename__ = "document_permissions"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    can_view: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    can_download: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    can_edit: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    granted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "document_id", name="uq_user_document_permission"),
    )

    # Relationships
    document = relationship("Document", foreign_keys=[document_id], backref="explicit_permissions")
    user = relationship("User", foreign_keys=[user_id], backref="document_permissions")
    granter = relationship("User", foreign_keys=[granted_by])
