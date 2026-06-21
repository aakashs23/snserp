"""initial_schema_v1

Revision ID: 001
Revises: 
Create Date: 2026-06-21

Creates all Version 1 database tables for Sri Naga Sai ERP.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Roles ────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # ── Permissions ──────────────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "permission_key", sa.String(100), unique=True, nullable=False
        ),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # ── Role-Permissions (association) ───────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "permission_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("permissions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    # ── Users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column(
            "role_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("roles.id"),
            nullable=False,
        ),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), server_default="true", nullable=False
        ),
        sa.Column(
            "last_login", sa.DateTime(timezone=True), nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role_id", "users", ["role_id"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # ── Customers ────────────────────────────────────────────────────────
    op.create_table(
        "customers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("customer_name", sa.String(150), nullable=False),
        sa.Column("gst_number", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("bank_name", sa.String(120), nullable=True),
        sa.Column("bank_account", sa.Text(), nullable=True),
        sa.Column("ifsc_code", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_customers_customer_name", "customers", ["customer_name"])
    op.create_index("ix_customers_gst_number", "customers", ["gst_number"])

    # ── Invoices ─────────────────────────────────────────────────────────
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "invoice_number", sa.String(50), unique=True, nullable=False
        ),
        sa.Column(
            "customer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("customers.id"),
            nullable=False,
        ),
        sa.Column("invoice_date", sa.Date(), nullable=False),
        sa.Column("month_of_supply", sa.Date(), nullable=True),
        sa.Column("payment_mode", sa.String(30), nullable=True),
        sa.Column("units", sa.Numeric(15, 3), nullable=True),
        sa.Column("rate", sa.Numeric(15, 4), nullable=True),
        sa.Column("gross_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "open_access_charges",
            sa.Numeric(15, 2),
            server_default="0",
            nullable=True,
        ),
        sa.Column("net_amount", sa.Numeric(15, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("pdf_storage_path", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.String(20), server_default="draft", nullable=True
        ),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_invoices_invoice_number", "invoices", ["invoice_number"], unique=True)
    op.create_index("ix_invoices_customer_id", "invoices", ["customer_id"])
    op.create_index("ix_invoices_invoice_date", "invoices", ["invoice_date"])
    op.create_index("ix_invoices_payment_date", "invoices", ["payment_date"])
    op.create_index("ix_invoices_status", "invoices", ["status"])
    op.create_index("ix_invoices_month_of_supply", "invoices", ["month_of_supply"])

    # ── Documents ────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=True),
        sa.Column("mime_type", sa.String(120), nullable=True),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("ai_category", sa.String(80), nullable=True),
        sa.Column(
            "uploaded_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "upload_date",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checksum_sha256", sa.String(64), nullable=True),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column(
            "is_deleted", sa.Boolean(), server_default="false"
        ),
    )
    op.create_index("ix_documents_category", "documents", ["category"])
    op.create_index("ix_documents_ai_category", "documents", ["ai_category"])
    op.create_index("ix_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("ix_documents_upload_date", "documents", [sa.text("upload_date DESC")])
    op.create_index("ix_documents_is_deleted", "documents", ["is_deleted"])
    op.create_index("ix_documents_checksum", "documents", ["checksum_sha256"])
    op.create_index("ix_documents_file_name", "documents", ["file_name"])

    # ── Document Metadata ────────────────────────────────────────────────
    op.create_table(
        "document_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("keywords", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("confidence_score", sa.Numeric(5, 2), nullable=True),
    )

    # ── Document AI ──────────────────────────────────────────────────────
    op.create_table(
        "document_ai",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column(
            "embedding_status",
            sa.String(30),
            server_default="pending",
        ),
        sa.Column("chromadb_id", sa.String(120), nullable=True),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True), nullable=True
        ),
    )

    # ── Activity Logs ────────────────────────────────────────────────────
    op.create_table(
        "activity_logs",
        sa.Column(
            "id", sa.BigInteger(), primary_key=True, autoincrement=True
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_activity_logs_user_id", "activity_logs", ["user_id"])
    op.create_index("ix_activity_logs_created_at", "activity_logs", [sa.text("created_at DESC")])
    op.create_index("ix_activity_logs_action", "activity_logs", ["action"])

    # ── AI Chat Sessions ─────────────────────────────────────────────────
    op.create_table(
        "ai_chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_chat_sessions_user_id", "ai_chat_sessions", ["user_id"])

    # ── AI Chat Messages ─────────────────────────────────────────────────
    op.create_table(
        "ai_chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("ai_chat_sessions.id"),
            nullable=False,
        ),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_ai_chat_messages_session_id", "ai_chat_messages", ["session_id"])

    # ── Notifications ────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "is_read", sa.Boolean(), server_default="false"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── Loans ────────────────────────────────────────────────────────────
    op.create_table(
        "loans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("loan_name", sa.String(200), nullable=False),
        sa.Column("bank_name", sa.String(150), nullable=False),
        sa.Column("principal_amount", sa.Numeric(15, 2), nullable=False),
        sa.Column(
            "interest_rate_annual",
            sa.Numeric(5, 2),
            nullable=False,
            comment="Annual interest rate as percentage",
        ),
        sa.Column(
            "tenure_months",
            sa.Integer(),
            nullable=False,
            comment="Loan tenure in months",
        ),
        sa.Column(
            "emi_amount",
            sa.Numeric(15, 2),
            nullable=True,
            comment="Monthly EMI amount",
        ),
        sa.Column("disbursement_date", sa.Date(), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("outstanding_balance", sa.Numeric(15, 2), nullable=True),
        sa.Column("total_interest_payable", sa.Numeric(15, 2), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            server_default="active",
            nullable=False,
            comment="active, closed, defaulted",
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ── GIN Index for document keywords ──────────────────────────────────
    op.execute(
        "CREATE INDEX ix_document_metadata_keywords ON document_metadata "
        "USING GIN (keywords)"
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.execute("DROP INDEX IF EXISTS ix_document_metadata_keywords")
    op.drop_table("loans")
    op.drop_table("notifications")
    op.drop_table("ai_chat_messages")
    op.drop_table("ai_chat_sessions")
    op.drop_table("activity_logs")
    op.drop_table("document_ai")
    op.drop_table("document_metadata")
    op.drop_table("documents")
    op.drop_table("invoices")
    op.drop_table("customers")
    op.drop_table("users")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
