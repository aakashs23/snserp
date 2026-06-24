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

import pandas as pd
import math
from fastapi import File, UploadFile

@router.post("/parse-excel")
async def parse_excel(
    file: UploadFile = File(...),
    _current_user: User = Depends(get_current_user),
) -> dict:
    """Parse an uploaded Excel file for invoice generation with flexible 2D template parsing."""
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="This file is not a valid Excel document.")
    
    try:
        # Read without headers to parse free-form grids
        df = pd.read_excel(file.file, header=None)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read the Excel file. It may be corrupted or unsupported.")
    
    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded Excel file contains no invoice data.")
        
    grid = df.values.tolist()
    extracted = {}

    def find_cell_with_text(text_variations):
        for r_idx, row in enumerate(grid):
            for c_idx, cell in enumerate(row):
                if isinstance(cell, str):
                    clean_cell = str(cell).strip().lower()
                    for t in text_variations:
                        if t in clean_cell:
                            return r_idx, c_idx
        return None, None

    def get_numbers_in_row(r_idx, start_c_idx):
        nums = []
        if r_idx is not None and r_idx < len(grid):
            for c_idx in range(start_c_idx + 1, len(grid[r_idx])):
                val = grid[r_idx][c_idx]
                if isinstance(val, (int, float)) and not math.isnan(val):
                    nums.append(val)
        return nums

    # 1. Customer Name
    # Usually directly above "HT SC No." in the template
    r_idx, c_idx = find_cell_with_text(["ht sc no", "ht sc number"])
    if r_idx is not None and r_idx > 0:
        val = grid[r_idx - 1][c_idx]
        if isinstance(val, str) and str(val).strip():
            extracted["Customer Name"] = str(val).strip()

    # Fallback for tabular: look for "Customer Name" in top rows
    if "Customer Name" not in extracted:
        r_idx, c_idx = find_cell_with_text(["customer name", "client name"])
        if r_idx is not None and r_idx + 1 < len(grid):
            val = grid[r_idx + 1][c_idx]
            if isinstance(val, str) and str(val).strip():
                extracted["Customer Name"] = str(val).strip()

    # 2. Quantity Units
    r_idx, c_idx = find_cell_with_text(["solar alloted", "alloted units", "quantity units"])
    if r_idx is not None:
        nums = get_numbers_in_row(r_idx, c_idx)
        if nums:
            extracted["Quantity Units"] = nums[0]

    # 3. Per Unit Rate
    # In the template, it's the first number next to "Invoice Amount"
    r_idx, c_idx = find_cell_with_text(["invoice amount", "amount"])
    if r_idx is not None:
        nums = get_numbers_in_row(r_idx, c_idx)
        if len(nums) > 0:
            extracted["Per Unit Rate"] = nums[0]

    # Fallback: standard "per unit rate"
    if "Per Unit Rate" not in extracted:
        r_idx, c_idx = find_cell_with_text(["per unit rate", "rate"])
        if r_idx is not None:
            nums = get_numbers_in_row(r_idx, c_idx)
            if nums:
                extracted["Per Unit Rate"] = nums[0]
            elif r_idx + 1 < len(grid):
                val = grid[r_idx + 1][c_idx]
                if isinstance(val, (int, float)) and not math.isnan(val):
                    extracted["Per Unit Rate"] = val

    # 4. Open Access Charges
    # Template has this at the bottom with a number next to it
    for r_idx, row in enumerate(grid):
        for c_idx, cell in enumerate(row):
            if isinstance(cell, str) and "open access" in str(cell).strip().lower():
                nums = get_numbers_in_row(r_idx, c_idx)
                if nums:
                    extracted["Open Access Charges"] = nums[-1]

    # 5. Round Off
    r_idx, c_idx = find_cell_with_text(["round off", "round"])
    if r_idx is not None:
        nums = get_numbers_in_row(r_idx, c_idx)
        if nums:
            extracted["Round Off"] = nums[0]

    found_fields = list(extracted.keys())
    missing_fields = [f for f in ["Customer Name", "Quantity Units", "Per Unit Rate", "Open Access Charges", "Round Off"] if f not in found_fields]

    if not found_fields:
        raise HTTPException(status_code=400, detail="Spreadsheet contains no recognizable invoice fields. Ensure you are using the correct template.")

    return {
        "data": extracted,
        "found_fields": found_fields,
        "missing_fields": missing_fields
    }
