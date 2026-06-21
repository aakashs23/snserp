"""Customer model."""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDPrimaryKeyMixin


class Customer(UUIDPrimaryKeyMixin, Base):
    """Customer / buyer to whom invoices are issued."""

    __tablename__ = "customers"

    customer_name: Mapped[str] = mapped_column(String(150), nullable=False)
    gst_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # encrypted at app level
    ifsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # relationships
    invoices: Mapped[list["Invoice"]] = relationship(
        "Invoice", back_populates="customer"
    )
