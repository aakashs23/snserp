"""Pydantic schemas for Invoice CRUD operations."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.schemas.customers import CustomerResponse

# Bounds mirror the column widths in models/invoices.py, so oversized input is
# rejected with a 422 instead of reaching Postgres. TEXT columns get a
# defensive cap rather than being unbounded.
_MAX_NOTES = 5000


class InvoiceCreate(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50)
    customer_id: UUID
    invoice_date: date
    month_of_supply: Optional[date] = None
    payment_mode: Optional[str] = Field(None, max_length=30)
    units: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    open_access_charges: Optional[Decimal] = Decimal("0")
    net_amount: Optional[Decimal] = None
    description: Optional[str] = Field(None, max_length=_MAX_NOTES)
    round_off: Optional[Decimal] = Decimal("0")
    notes: Optional[str] = Field(None, max_length=_MAX_NOTES)
    status: Optional[str] = Field("draft", max_length=20)


class InvoiceUpdate(BaseModel):
    customer_id: Optional[UUID] = None
    invoice_date: Optional[date] = None
    month_of_supply: Optional[date] = None
    payment_mode: Optional[str] = Field(None, max_length=30)
    units: Optional[Decimal] = None
    rate: Optional[Decimal] = None
    gross_amount: Optional[Decimal] = None
    open_access_charges: Optional[Decimal] = None
    net_amount: Optional[Decimal] = None
    description: Optional[str] = Field(None, max_length=_MAX_NOTES)
    round_off: Optional[Decimal] = None
    notes: Optional[str] = Field(None, max_length=_MAX_NOTES)
    status: Optional[str] = Field(None, max_length=20)
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
    description: Optional[str] = None
    round_off: Optional[Decimal] = None
    notes: Optional[str] = None
    pdf_storage_path: Optional[str] = None
    status: Optional[str] = None
    payment_date: Optional[date] = None
    created_by: UUID
    created_at: datetime
    updated_at: datetime
    
    customer: Optional[CustomerResponse] = None
