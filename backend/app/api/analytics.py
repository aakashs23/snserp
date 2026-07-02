from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from decimal import Decimal
import datetime

from app.database.session import get_db
from app.models.invoices import Invoice
from app.models.customers import Customer
from app.models.users import User
from app.middleware.auth import get_current_user
from app.schemas.analytics import RevenueDashboardResponse, MonthlyRevenueItem, TopCustomerItem

router = APIRouter()

@router.get("/revenue", response_model=RevenueDashboardResponse)
async def get_revenue_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_year = datetime.date.today().year

    # 1. Total YTD Revenue
    ytd_query = select(func.sum(Invoice.net_amount)).where(
        func.extract('year', Invoice.invoice_date) == current_year,
        Invoice.status != 'cancelled'
    )
    ytd_result = await db.execute(ytd_query)
    total_ytd = ytd_result.scalar_one_or_none() or Decimal('0.00')

    # 2. Invoice Counts
    counts_query = select(
        func.count(Invoice.id).label('total'),
        func.count(Invoice.id).filter(Invoice.status == 'paid').label('paid'),
        func.count(Invoice.id).filter(Invoice.status == 'sent').label('pending'),
    ).where(func.extract('year', Invoice.invoice_date) == current_year)
    counts_result = await db.execute(counts_query)
    counts = counts_result.one()
    
    total_inv = counts.total or 0
    paid_inv = counts.paid or 0
    pending_inv = counts.pending or 0

    # 3. Monthly Trend (Using raw SQL for simpler aggregation over months)
    # PostgreSQL specific grouping by month text (YYYY-MM)
    monthly_sql = text("""
        SELECT 
            to_char(invoice_date, 'YYYY-MM') as month,
            COALESCE(SUM(net_amount), 0) as revenue,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN net_amount ELSE 0 END), 0) as paid,
            COALESCE(SUM(CASE WHEN status != 'paid' AND status != 'cancelled' THEN net_amount ELSE 0 END), 0) as pending
        FROM invoices
        WHERE EXTRACT(YEAR FROM invoice_date) = :year
        GROUP BY month
        ORDER BY month ASC
    """)
    monthly_res = await db.execute(monthly_sql, {"year": current_year})
    monthly_trend = []
    for row in monthly_res.mappings():
        monthly_trend.append(MonthlyRevenueItem(
            month=row['month'],
            revenue=Decimal(str(row['revenue'])),
            paid=Decimal(str(row['paid'])),
            pending=Decimal(str(row['pending']))
        ))

    # 4. Top Customers
    top_customers_sql = text("""
        SELECT c.customer_name, COALESCE(SUM(i.net_amount), 0) as revenue
        FROM invoices i
        JOIN customers c ON i.customer_id = c.id
        WHERE EXTRACT(YEAR FROM i.invoice_date) = :year AND i.status != 'cancelled'
        GROUP BY c.id, c.customer_name
        ORDER BY revenue DESC
        LIMIT 5
    """)
    tc_res = await db.execute(top_customers_sql, {"year": current_year})
    top_customers = []
    for row in tc_res.mappings():
        top_customers.append(TopCustomerItem(
            customer_name=row['customer_name'],
            revenue=Decimal(str(row['revenue']))
        ))

    return RevenueDashboardResponse(
        total_revenue_ytd=total_ytd,
        total_invoices_generated=total_inv,
        pending_invoices_count=pending_inv,
        paid_invoices_count=paid_inv,
        monthly_trend=monthly_trend,
        top_customers=top_customers
    )

from app.models.documents import Document
from app.models.loans import Loan
from app.models.activity import ActivityLog
from app.schemas.analytics import DashboardStatsResponse
from app.api.activity import ActivityLogResponse

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    import datetime
    current_month = datetime.date.today().month
    current_year = datetime.date.today().year

    # 1. Monthly Revenue
    rev_query = select(func.sum(Invoice.net_amount)).where(
        func.extract('month', Invoice.invoice_date) == current_month,
        func.extract('year', Invoice.invoice_date) == current_year,
        Invoice.status != 'cancelled'
    )
    rev_result = await db.execute(rev_query)
    monthly_rev = rev_result.scalar_one_or_none() or Decimal('0.00')

    # 2. Total Invoices
    inv_query = select(func.count(Invoice.id))
    inv_result = await db.execute(inv_query)
    total_invoices = inv_result.scalar_one_or_none() or 0

    # 3. Total Documents
    doc_query = select(func.count(Document.id)).where(Document.is_deleted == False)
    doc_result = await db.execute(doc_query)
    total_documents = doc_result.scalar_one_or_none() or 0

    # 4. Active Customers
    cust_query = select(func.count(Customer.id))
    cust_result = await db.execute(cust_query)
    active_customers = cust_result.scalar_one_or_none() or 0
    
    # 5. Active Loans
    loan_query = select(func.count(Loan.id)).where(Loan.status == 'active')
    loan_result = await db.execute(loan_query)
    active_loans = loan_result.scalar_one_or_none() or 0

    return DashboardStatsResponse(
        monthly_revenue=monthly_rev,
        total_invoices=total_invoices,
        total_documents=total_documents,
        active_customers=active_customers,
        active_loans=active_loans
    )

@router.get("/dashboard/activity", response_model=list[ActivityLogResponse])
async def get_dashboard_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import desc
    stmt = (
        select(ActivityLog, User.full_name, User.email)
        .outerjoin(User, ActivityLog.user_id == User.id)
        .order_by(desc(ActivityLog.created_at))
        .limit(5)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    activities = []
    for row in rows:
        log_obj = row[0]
        # Attach user properties temporarily for Pydantic
        log_obj.user_name = row[1]
        log_obj.user_email = row[2]
        activities.append(log_obj)
        
    return activities
