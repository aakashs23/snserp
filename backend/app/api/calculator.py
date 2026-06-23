from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal, ROUND_HALF_UP

from app.models.users import User
from app.middleware.auth import get_current_user

router = APIRouter()

class CalculatorRequest(BaseModel):
    units_generated: float = Field(..., ge=0)
    withdrawal_loss_percent: float = Field(..., ge=0, le=100)
    injection_loss_percent: float = Field(..., ge=0, le=100)
    per_unit_rate: float = Field(..., ge=0)
    open_access_charges: float = Field(default=0.0, ge=0)
    manual_round_off: Optional[float] = None

class CalculatorResponse(BaseModel):
    withdrawal_loss_units: float
    injection_loss_units: float
    total_line_loss_units: float
    sellable_units: float
    gross_revenue: float
    generation_tax: float
    agent_commission: float
    applied_round_off: float
    final_net_income: float

@router.post("/calculate", response_model=CalculatorResponse)
async def calculate_monthly_invoice(
    request: CalculatorRequest,
    current_user: User = Depends(get_current_user)
):
    units = Decimal(str(request.units_generated))
    wd_loss_pct = Decimal(str(request.withdrawal_loss_percent)) / Decimal('100')
    inj_loss_pct = Decimal(str(request.injection_loss_percent)) / Decimal('100')
    rate = Decimal(str(request.per_unit_rate))
    oac = Decimal(str(request.open_access_charges))
    
    # Step 1: Withdrawal Loss Units
    wd_loss_units = units * wd_loss_pct
    
    # Step 2: Injection Loss Units
    inj_loss_units = units * inj_loss_pct
    
    # Step 3: Total Line Loss Units
    total_loss_units = wd_loss_units + inj_loss_units
    
    # Step 4: Sellable Units
    sellable_units = units - total_loss_units
    
    # Step 5: Gross Revenue (Rounded to whole number to end in .00)
    gross_revenue_raw = sellable_units * rate
    gross_revenue = gross_revenue_raw.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    
    # Step 6: Generation Tax (0.63 * Sellable Units)
    gen_tax_raw = Decimal('0.63') * sellable_units
    gen_tax = gen_tax_raw.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    
    # Step 7: Agent Commission (0.10 * Sellable Units)
    agent_comm_raw = Decimal('0.10') * sellable_units
    agent_comm = agent_comm_raw.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
    
    # Step 8: Net Income
    net_income_raw = gross_revenue - oac - gen_tax - agent_comm
    
    # Rounding Logic
    if request.manual_round_off is not None:
        applied_round_off = Decimal(str(request.manual_round_off))
    else:
        # Automatic rounding to the nearest integer
        rounded_net = net_income_raw.quantize(Decimal('1.'), rounding=ROUND_HALF_UP)
        applied_round_off = rounded_net - net_income_raw
        
    final_net_income = net_income_raw + applied_round_off
    
    return CalculatorResponse(
        withdrawal_loss_units=float(wd_loss_units),
        injection_loss_units=float(inj_loss_units),
        total_line_loss_units=float(total_loss_units),
        sellable_units=float(sellable_units),
        gross_revenue=float(gross_revenue),
        generation_tax=float(gen_tax),
        agent_commission=float(agent_comm),
        applied_round_off=float(applied_round_off),
        final_net_income=float(final_net_income)
    )
