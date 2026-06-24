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
from app.models.customers import Customer
from app.repositories.base import BaseRepository
from app.schemas.invoices import InvoiceCreate, InvoiceResponse, InvoiceUpdate
from app.services.pdf_generator import generate_invoice_pdf
from app.config.supabase import supabase

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
    
    # 1. Save to DB first to get the ID
    invoice = await repo.create(data)
    
    # 2. Fetch Customer for PDF
    customer_res = await db.execute(select(Customer).where(Customer.id == invoice.customer_id))
    customer = customer_res.scalar_one_or_none()
    
    if customer:
        # 3. Generate PDF
        pdf_bytes = generate_invoice_pdf(invoice, customer)
        
        # 4. Upload to Supabase
        file_path = f"{current_user.id}/{invoice.id}.pdf"
        try:
            # Ensure bucket exists (ignore error if it does)
            try:
                supabase.storage.create_bucket("invoice-pdfs", options={"public": False})
            except Exception:
                pass
                
            supabase.storage.from_("invoice-pdfs").upload(
                file_path, 
                pdf_bytes, 
                file_options={"content-type": "application/pdf", "upsert": "true"}
            )
            
            # 5. Update invoice with path
            await repo.update(invoice, {"pdf_storage_path": file_path})
        except Exception as e:
            print(f"Failed to upload PDF: {e}")
            
    # Refresh to get relations properly
    query = select(Invoice).options(selectinload(Invoice.customer)).where(Invoice.id == invoice.id)
    result = await db.execute(query)
    return result.scalar_one()


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


@router.get("/{invoice_id}/pdf")
async def get_invoice_pdf(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Get a signed URL for the invoice PDF."""
    repo = BaseRepository(Invoice, db)
    invoice = await repo.get(invoice_id)
    if not invoice or not invoice.pdf_storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice PDF not found",
        )
    
    try:
        # Create a signed URL valid for 1 hour (3600 seconds)
        response = supabase.storage.from_("invoice-pdfs").create_signed_url(
            invoice.pdf_storage_path, 3600
        )
        if "signedURL" in response:
            return {"url": response["signedURL"]}
        raise HTTPException(status_code=500, detail="Could not generate signed URL")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
