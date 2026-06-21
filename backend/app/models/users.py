"""User, Role, and Permission models."""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# ── Association table (many-to-many: Role ↔ Permission) ─────────────────────
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ── Role ─────────────────────────────────────────────────────────────────────
class Role(UUIDPrimaryKeyMixin, Base):
    """Application role (e.g. admin, accountant, viewer)."""

    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="role")
    permissions: Mapped[list["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
    )


# ── Permission ───────────────────────────────────────────────────────────────
class Permission(UUIDPrimaryKeyMixin, Base):
    """Granular permission key (e.g. invoices.create, reports.view)."""

    __tablename__ = "permissions"

    permission_key: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    roles: Mapped[list["Role"]] = relationship(
        "Role",
        secondary=role_permissions,
        back_populates="permissions",
    )


# ── User ─────────────────────────────────────────────────────────────────────
class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Application user, linked 1-to-1 with Supabase Auth UID."""

    __tablename__ = "users"

    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("roles.id"), nullable=False
    )
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )
    last_login: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relationships — same file
    role: Mapped["Role"] = relationship("Role", back_populates="users")

    # relationships — other files (string references, resolved at runtime)
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="creator"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="uploader"
    )
    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user"
    )
    chat_sessions: Mapped[list["AIChatSession"]] = relationship(
        "AIChatSession", back_populates="user"
    )
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
