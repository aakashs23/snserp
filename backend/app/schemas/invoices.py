"""Pydantic schemas for Invoice CRUD operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field


class InvoiceCreate(BaseModel):
    invoice_number: str
    customer_id: UUID
    invoice_date: date
    month_of_supply: Optional[date] = None
    payment_mode: Optional[str] = None
    units: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    open_access_charges: Optional[Decimal] = Decimal("0")
    net_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = "draft"


class InvoiceUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    month_of_supply: Optional[date] = None
    payment_mode: Optional[str] = None
    units: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    open_access_charges: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    payment_date: Optional[date] = None


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    invoice_number: str
    customer_id: UUID
    invoice_date: date
    month_of_supply: Optional[date] = None
    payment_mode: Optional[str] = None
    units: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    open_access_charges: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    pdf_storage_path: Optional[str] = None
    status: Optional[str] = None
    payment_date: Optional[date] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def gst_amount(self) -> Optional[Decimal]:
        """18% GST calculated dynamically."""
        if self.gross_amount:
            return round(self.gross_amount * Decimal("0.18"), 2)
        return None

    @computed_field
    @property
    def tds_amount(self) -> Optional[Decimal]:
        """1% TDS calculated dynamically."""
        if self.gross_amount:
            return round(self.gross_amount * Decimal("0.01"), 2)
        return None
