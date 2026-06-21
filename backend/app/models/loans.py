"""Loan model for bank loan tracking and amortization."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Loan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Bank loan details for dashboard amortization tracking."""

    __tablename__ = "loans"

    loan_name: Mapped[str] = mapped_column(
        String(200), nullable=False
    )
    bank_name: Mapped[str] = mapped_column(
        String(150), nullable=False
    )
    principal_amount: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False
    )
    interest_rate_annual: Mapped[float] = mapped_column(
        Numeric(5, 2), nullable=False, comment="Annual interest rate as percentage"
    )
    tenure_months: Mapped[int] = mapped_column(
        nullable=False, comment="Loan tenure in months"
    )
    emi_amount: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Monthly EMI amount"
    )
    disbursement_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False
    )
    end_date: Mapped[date | None] = mapped_column(
        Date, nullable=True
    )
    outstanding_balance: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    total_interest_payable: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False,
        comment="active, closed, defaulted",
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )
