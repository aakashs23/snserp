"""Pydantic schemas for Customer CRUD operations."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreate(BaseModel):
    customer_name: str = Field(..., min_length=1)
    gst_number: str = Field(..., pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    address: str = Field(..., min_length=1)
    ht_sc_number: str = Field(..., min_length=1)


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = None
    gst_number: Optional[str] = Field(None, pattern=r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")
    address: Optional[str] = None
    ht_sc_number: Optional[str] = None


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    customer_name: str
    gst_number: Optional[str] = None
    address: Optional[str] = None
    ht_sc_number: Optional[str] = None
    created_at: datetime

