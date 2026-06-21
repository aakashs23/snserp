"""Invoice model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Invoice(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Sales invoice issued to a customer.

    NOTE: GST and TDS amounts are **not** stored — they are calculated
    dynamically at query / serialisation time.
    """

    __tablename__ = "invoices"

    invoice_number: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False
    )
    invoice_date: Mapped[date] = mapped_column(Date, nullable=False)
    month_of_supply: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_mode: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # monetary / quantity fields
    units: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)
    rate: Mapped[float | None] = mapped_column(Numeric(15, 4), nullable=True)
    gross_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    open_access_charges: Mapped[float | None] = mapped_column(
        Numeric(15, 2), server_default="0", nullable=True
    )
    net_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_storage_path: Mapped[str | None] = mapped_column(Text, nullable=True)

    # status: draft | sent | paid | overdue | cancelled
    status: Mapped[str | None] = mapped_column(
        String(20), server_default="draft", nullable=True
    )
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )

    # relationships
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="invoices"
    )
    creator: Mapped["User"] = relationship("User", back_populates="invoices")
