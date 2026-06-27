"""SQLAlchemy models for Sri Naga Sai ERP.

Importing this module ensures all models are registered with the
SQLAlchemy metadata, which is required for Alembic auto-generation.
"""

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.users import Role, Permission, role_permissions, User
from app.models.customers import Customer
from app.models.invoices import Invoice
from app.models.documents import Document, DocumentMetadata, DocumentAI
from app.models.document_permissions import DocumentPermission
from app.models.activity import ActivityLog
from app.models.chat import AIChatSession, AIChatMessage
from app.models.notifications import Notification
from app.models.loans import Loan

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # Auth & Users
    "Role",
    "Permission",
    "role_permissions",
    "User",
    # Business
    "Customer",
    "Invoice",
    "Loan",
    # Documents
    "Document",
    "DocumentMetadata",
    "DocumentAI",
    "DocumentPermission",
    # Activity & Chat
    "ActivityLog",
    "AIChatSession",
    "AIChatMessage",
    # Notifications
    "Notification",
]
