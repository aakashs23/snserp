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

router = APIRouter()


@router.get("/", response_model=list[CustomerResponse])
async def list_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None, description="Search by customer name"),
    db: AsyncSession = Depends(get_db),
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
    return updated


@router.delete(
    "/{customer_id}",
    dependencies=[Depends(RequireRole(["admin"]))],
)
async def delete_customer(
    customer_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Delete a customer. Requires admin role."""
    repo = BaseRepository(Customer, db)
    deleted = await repo.delete(customer_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )
    return {"deleted": True}
