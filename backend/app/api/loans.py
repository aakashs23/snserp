import datetime
import calendar
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.models.loans import Loan
from app.models.users import User
from app.repositories.base import BaseRepository
from app.schemas.loans import LoanCreate, LoanResponse, LoanUpdate

router = APIRouter()

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    return datetime.date(year, month, day)

@router.get("/dashboard")
async def get_loans_dashboard(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> dict:
    """Get high-level aggregated metrics for loans."""
    query = select(Loan).where(Loan.status == "active")
    result = await db.execute(query)
    loans = result.scalars().all()
    
    total_outstanding = 0
    total_interest_remaining = 0
    total_emi_remaining = 0
    total_emi_paid = 0
    next_due_date = None
    
    today = datetime.date.today()
    
    for loan in loans:
        p = loan.principal_amount
        r = loan.interest_rate_annual / 12 / 100
        n = loan.tenure_months
        
        if r > 0:
            emi = p * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
        else:
            emi = p / n if n > 0 else 0
            
        current_date = loan.start_date
        balance = p
        
        for i in range(1, n + 1):
            if balance <= 0:
                break
                
            if r > 0:
                interest = balance * r
                principal = emi - interest
            else:
                interest = 0
                principal = emi
                
            if i == n:
                principal = balance
                emi = principal + interest
                balance = 0
            else:
                balance -= principal
                
            if current_date < today:
                total_emi_paid += emi
            else:
                total_outstanding += principal
                total_interest_remaining += interest
                total_emi_remaining += emi
                if not next_due_date or current_date < next_due_date:
                    next_due_date = current_date
                    
            current_date = add_months(current_date, 1)

    return {
        "outstanding_balance": round(total_outstanding, 2),
        "total_interest_remaining": round(total_interest_remaining, 2),
        "total_emi_remaining": round(total_emi_remaining, 2),
        "total_emi_paid": round(total_emi_paid, 2),
        "next_due_date": next_due_date.strftime("%Y-%m-%d") if next_due_date else None
    }


@router.get("/", response_model=list[LoanResponse])
async def list_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[LoanResponse]:
    """List all loans."""
    query = select(Loan).order_by(Loan.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def create_loan(
    body: LoanCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin", "accountant", "employee"])),
) -> LoanResponse:
    repo = BaseRepository(Loan, db)
    return await repo.create(body.model_dump())


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> LoanResponse:
    repo = BaseRepository(Loan, db)
    loan = await repo.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    return loan


@router.put("/{loan_id}", response_model=LoanResponse)
async def update_loan(
    loan_id: UUID,
    body: LoanUpdate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin", "accountant", "employee"])),
) -> LoanResponse:
    repo = BaseRepository(Loan, db)
    loan = await repo.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    updated = await repo.update(loan, body.model_dump(exclude_unset=True))
    return updated


@router.delete("/{loan_id}")
async def delete_loan(
    loan_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(RequireRole(["admin", "accountant", "employee"])),
) -> dict:
    repo = BaseRepository(Loan, db)
    deleted = await repo.delete(loan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Loan not found")
    return {"deleted": True}


@router.get("/{loan_id}/amortization")
async def get_loan_amortization(
    loan_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user)
) -> dict:
    repo = BaseRepository(Loan, db)
    loan = await repo.get(loan_id)
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
        
    p = loan.principal_amount
    r = loan.interest_rate_annual / 12 / 100
    n = loan.tenure_months
    
    if r > 0:
        emi = p * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)
    else:
        emi = p / n if n > 0 else 0
        
    schedule = []
    balance = p
    current_date = loan.start_date
    
    total_interest = 0
    total_paid = 0
    
    for i in range(1, n + 1):
        if r > 0:
            interest = balance * r
            principal = emi - interest
        else:
            interest = 0
            principal = emi
            
        if i == n:
            principal = balance
            emi = principal + interest
            balance = 0
        else:
            balance -= principal
            
        schedule.append({
            "installment": i,
            "date": current_date.strftime("%Y-%m-%d"),
            "emi": round(emi, 2),
            "principal": round(principal, 2),
            "interest": round(interest, 2),
            "remaining_balance": round(max(0, balance), 2)
        })
        current_date = add_months(current_date, 1)
        total_interest += interest
        total_paid += emi
        
    return {
        "schedule": schedule,
        "summary": {
            "total_interest": round(total_interest, 2),
            "total_paid": round(total_paid, 2),
            "emi": round(emi, 2) if n > 0 else 0
        }
    }
