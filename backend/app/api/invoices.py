"""Invoices API router — full CRUD with filtering."""

from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.models.invoices import Invoice
from app.models.users import User
from app.repositories.base import BaseRepository
from app.schemas.invoices import InvoiceCreate, InvoiceResponse, InvoiceUpdate

router = APIRouter()


@router.get("/", response_model=list[InvoiceResponse])
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by invoice status"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer ID"),
    from_date: Optional[date] = Query(None, description="Invoice date from (inclusive)"),
    to_date: Optional[date] = Query(None, description="Invoice date to (inclusive)"),
    db: AsyncSession = Depends(get_db),
) -> list[InvoiceResponse]:
    """List invoices with optional filters and pagination. Eagerly loads customer."""
    query = select(Invoice).options(selectinload(Invoice.customer))

    if status_filter:
        query = query.where(Invoice.status == status_filter)
    if customer_id:
        query = query.where(Invoice.customer_id == customer_id)
    if from_date:
        query = query.where(Invoice.invoice_date >= from_date)
    if to_date:
        query = query.where(Invoice.invoice_date <= to_date)

    query = query.order_by(Invoice.invoice_date.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> InvoiceResponse:
    """Get a single invoice by ID."""
    query = (
        select(Invoice)
        .options(selectinload(Invoice.customer))
        .where(Invoice.id == invoice_id)
    )
    result = await db.execute(query)
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return invoice


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InvoiceResponse:
    """Create a new invoice. Sets created_by from the authenticated user."""
    repo = BaseRepository(Invoice, db)
    data = body.model_dump()
    data["created_by"] = current_user.id
    invoice = await repo.create(data)
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    body: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> InvoiceResponse:
    """Update an existing invoice. Requires authentication."""
    repo = BaseRepository(Invoice, db)
    invoice = await repo.get(invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    updated = await repo.update(invoice, body.model_dump(exclude_unset=True))
    return updated


@router.delete(
    "/{invoice_id}",
    dependencies=[Depends(RequireRole(["admin"]))],
)
async def delete_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete an invoice. Requires admin role."""
    repo = BaseRepository(Invoice, db)
    deleted = await repo.delete(invoice_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found",
        )
    return {"deleted": True}
