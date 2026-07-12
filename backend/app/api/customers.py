"""Customers API router — full CRUD."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.models.customers import Customer
from app.models.users import User
from app.repositories.base import BaseRepository
from app.schemas.customers import CustomerCreate, CustomerResponse, CustomerUpdate
from app.services.activity_service import log_activity

router = APIRouter()


@router.get("/export")
async def export_customers(
    format: str = Query("csv", description="Export format: csv, xlsx, or pdf"),
    search: Optional[str] = Query(None, description="Search by customer name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(RequireRole(["admin", "employee", "accountant"])),
):
    """Export customers data."""
    from app.services.export_service import generate_export_response
    
    query = select(Customer)
    if search:
        query = query.where(Customer.customer_name.ilike(f"%{search}%"))
        
    result = await db.execute(query)
    customers = result.scalars().all()
    
    data = []
    for c in customers:
        data.append({
            "customer_id": str(c.id),
            "customer_name": c.customer_name,
            "email": c.email,
            "phone": c.phone,
            "gst_number": c.gst_number,
            "address": c.address,
            "created_at": c.created_at,
        })
        
    return generate_export_response(data, format, "Customers Directory", current_user.full_name or current_user.email)

@router.get("/", response_model=list[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search by customer name"),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin", "employee", "accountant"])),
) -> list[CustomerResponse]:
    """List customers with optional name search and pagination."""
    if search:
        query = (
            select(Customer)
            .where(Customer.customer_name.ilike(f"%{search}%"))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        customers = result.scalars().all()
    else:
        repo = BaseRepository(Customer, db)
        customers = await repo.get_multi(skip=skip, limit=limit)
    return customers


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin", "employee", "accountant"])),
) -> CustomerResponse:
    """Get a single customer by ID."""
    repo = BaseRepository(Customer, db)
    customer = await repo.get(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return customer


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    body: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin"])),
) -> CustomerResponse:
    """Create a new customer. Requires authentication."""
    repo = BaseRepository(Customer, db)
    customer = await repo.create(body.model_dump())
    
    await log_activity(
        db=db,
        user_id=_current_user.id,
        action="Create",
        module="Customers",
        object_affected=f"Customer ID: {customer.id}"
    )
    await db.commit()
    
    return customer


@router.put("/{customer_id}", response_model=CustomerResponse)
async def update_customer(
    customer_id: UUID,
    body: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin"])),
) -> CustomerResponse:
    """Update an existing customer. Requires authentication."""
    repo = BaseRepository(Customer, db)
    customer = await repo.get(customer_id)
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    updated = await repo.update(customer, body.model_dump(exclude_unset=True))
    
    await log_activity(
        db=db,
        user_id=_current_user.id,
        action="Update",
        module="Customers",
        object_affected=f"Customer ID: {customer.id}"
    )
    await db.commit()
    
    return updated


@router.delete(
    "/{customer_id}",
    dependencies=[Depends(RequireRole(["admin"]))],
)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin"])),
) -> dict:
    """Delete a customer. Requires admin role."""
    repo = BaseRepository(Customer, db)
    deleted = await repo.delete(customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
        
    await log_activity(
        db=db,
        user_id=_current_user.id,
        action="Delete",
        module="Customers",
        object_affected=f"Customer ID: {customer_id}"
    )
    await db.commit()
    
    return {"deleted": True}
