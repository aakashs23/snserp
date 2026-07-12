from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

# String bounds mirror column widths in models/loans.py; notes is TEXT and gets a
# defensive cap. Amounts are constrained to non-negative to reject bad input early.
class LoanCreate(BaseModel):
    loan_name: str = Field(..., min_length=1, max_length=200)
    bank_name: str = Field(..., min_length=1, max_length=150)
    principal_amount: float = Field(..., gt=0)
    interest_rate_annual: float = Field(..., ge=0)
    tenure_months: int = Field(..., gt=0)
    emi_amount: Optional[float] = Field(None, ge=0)
    payment_frequency: str = Field("monthly", max_length=20)
    disbursement_date: Optional[date] = None
    start_date: date
    end_date: Optional[date] = None
    notes: Optional[str] = Field(None, max_length=5000)
    status: str = Field("active", max_length=20)
    outstanding_balance: Optional[float] = Field(None, ge=0)
    total_interest_payable: Optional[float] = Field(None, ge=0)

class LoanUpdate(BaseModel):
    loan_name: Optional[str] = Field(None, min_length=1, max_length=200)
    bank_name: Optional[str] = Field(None, min_length=1, max_length=150)
    principal_amount: Optional[float] = Field(None, gt=0)
    interest_rate_annual: Optional[float] = Field(None, ge=0)
    tenure_months: Optional[int] = Field(None, gt=0)
    emi_amount: Optional[float] = Field(None, ge=0)
    payment_frequency: Optional[str] = Field(None, max_length=20)
    disbursement_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = Field(None, max_length=5000)
    outstanding_balance: Optional[float] = Field(None, ge=0)
    total_interest_payable: Optional[float] = Field(None, ge=0)

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
