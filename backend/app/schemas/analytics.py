from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from typing import List, Optional

class MonthlyRevenueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    month: str
    revenue: Decimal
    paid: Decimal
    pending: Decimal

class TopCustomerItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    customer_name: str
    revenue: Decimal

class RevenueDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    total_revenue_ytd: Decimal
    total_invoices_generated: int
    pending_invoices_count: int
    paid_invoices_count: int
    monthly_trend: List[MonthlyRevenueItem]
    top_customers: List[TopCustomerItem]

class DashboardStatsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    monthly_revenue: Decimal
    total_invoices: int
    total_documents: int
    active_customers: int
    active_loans: int
