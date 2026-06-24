from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

class LoanCreate(BaseModel):
    loan_name: str = Field(..., min_length=1)
    bank_name: str = Field(..., min_length=1)
    principal_amount: float = Field(..., gt=0)
    interest_rate_annual: float = Field(..., ge=0)
    tenure_months: int = Field(..., gt=0)
    emi_amount: Optional[float] = None
    payment_frequency: str = "monthly"
    disbursement_date: Optional[date] = None
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = None
    status: str = "active"
    outstanding_balance: Optional[float] = None
    total_interest_payable: Optional[float] = None

class LoanUpdate(BaseModel):
    loan_name: Optional[str] = None
    bank_name: Optional[str] = None
    principal_amount: Optional[float] = None
    interest_rate_annual: Optional[float] = None
    tenure_months: Optional[int] = None
    emi_amount: Optional[float] = None
    payment_frequency: Optional[str] = None
    disbursement_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    outstanding_balance: Optional[float] = None
    total_interest_payable: Optional[float] = None

class LoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    loan_name: str
    bank_name: str
    principal_amount: float
    interest_rate_annual: float
    tenure_months: int
    emi_amount: Optional[float] = None
    payment_frequency: str
    disbursement_date: Optional[date] = None
    start_date: date
    end_date: Optional[date] = None
    status: str
    notes: Optional[str] = None
    outstanding_balance: Optional[float] = None
    total_interest_payable: Optional[float] = None
    created_at: datetime
