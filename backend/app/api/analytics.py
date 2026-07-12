from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from decimal import Decimal
import datetime

from app.database.session import get_db
from app.models.invoices import Invoice
from app.models.customers import Customer
from app.models.users import User
from app.middleware.auth import get_current_user
from app.middleware.rbac import RequireRole
from app.schemas.analytics import (
    RevenueDashboardResponse, MonthlyRevenueItem, TopCustomerItem,
    DashboardStatsResponse, InvoiceStatusItem, DocumentUploadItem, RecentRevenueItem
)
from app.models.documents import Document
from app.models.loans import Loan
from app.models.activity import ActivityLog
from app.api.activity import ActivityLogResponse

router = APIRouter()

@router.get("/revenue/export")
async def export_revenue(
    format: str = Query("csv", description="Export format: csv, xlsx, or pdf"),
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    """Export revenue dashboard data."""
    from app.services.export_service import generate_export_response
    current_year = datetime.date.today().year

    monthly_sql = text("""
        SELECT 
            to_char(invoice_date, 'YYYY-MM') as month,
            COALESCE(SUM(net_amount), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN status = 'paid' THEN net_amount ELSE 0 END), 0) as paid_revenue,
            COALESCE(SUM(CASE WHEN status != 'paid' AND status != 'cancelled' THEN net_amount ELSE 0 END), 0) as pending_revenue,
            COUNT(id) as total_invoices
        FROM invoices
        WHERE EXTRACT(YEAR FROM invoice_date) = :year
        GROUP BY month
        ORDER BY month ASC
    """)
    result = await db.execute(monthly_sql, {"year": current_year})
    rows = result.fetchall()
    
    data = []
    for row in rows:
        data.append({
            "month": row.month,
            "total_revenue": row.total_revenue,
            "paid_revenue": row.paid_revenue,
            "pending_revenue": row.pending_revenue,
            "total_invoices": row.total_invoices
        })
        
    return generate_export_response(data, format, f"Revenue Report {current_year}", current_user.full_name or current_user.email)

@router.get("/revenue", response_model=RevenueDashboardResponse)
async def get_revenue_dashboard(
    current_user: User = Depends(RequireRole(["admin", "employee"])),
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
    monthly_trend = [
        MonthlyRevenueItem(
            month=row['month'], revenue=Decimal(str(row['revenue'])),
            paid=Decimal(str(row['paid'])), pending=Decimal(str(row['pending']))
        ) for row in monthly_res.mappings()
    ]

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
    top_customers = [
        TopCustomerItem(customer_name=row['customer_name'], revenue=Decimal(str(row['revenue'])))
        for row in tc_res.mappings()
    ]

    return RevenueDashboardResponse(
        total_revenue_ytd=total_ytd, total_invoices_generated=total_inv,
        pending_invoices_count=pending_inv, paid_invoices_count=paid_inv,
        monthly_trend=monthly_trend, top_customers=top_customers
    )

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(RequireRole(["admin", "employee"])),
    db: AsyncSession = Depends(get_db)
):
    current_date = datetime.date.today()
    current_month = current_date.month
    current_year = current_date.year
    seven_days_ago = current_date - datetime.timedelta(days=7)

    # 1. Stats
    rev_query = select(func.sum(Invoice.net_amount)).where(
        func.extract('month', Invoice.invoice_date) == current_month,
        func.extract('year', Invoice.invoice_date) == current_year,
        Invoice.status != 'cancelled'
    )
    monthly_rev = (await db.execute(rev_query)).scalar_one_or_none() or Decimal('0.00')

    yr_query = select(func.sum(Invoice.net_amount)).where(
        func.extract('year', Invoice.invoice_date) == current_year,
        Invoice.status != 'cancelled'
    )
    yearly_rev = (await db.execute(yr_query)).scalar_one_or_none() or Decimal('0.00')

    total_customers = (await db.execute(select(func.count(Customer.id)))).scalar_one_or_none() or 0
    total_documents = (await db.execute(select(func.count(Document.id)).where(Document.is_deleted == False))).scalar_one_or_none() or 0
    
    inv_counts = (await db.execute(select(
        func.count(Invoice.id).label('total'),
        func.count(Invoice.id).filter(Invoice.status == 'paid').label('paid'),
        func.count(Invoice.id).filter(Invoice.status != 'paid').filter(Invoice.status != 'cancelled').label('pending'),
        func.sum(Invoice.net_amount).filter(Invoice.status != 'paid').filter(Invoice.status != 'cancelled').label('outstanding')
    ))).one()
    
    total_invoices = inv_counts.total or 0
    paid_invoices = inv_counts.paid or 0
    pending_invoices = inv_counts.pending or 0
    outstanding_amount = inv_counts.outstanding or Decimal('0.00')

    active_loans = (await db.execute(select(func.count(Loan.id)).where(Loan.status == 'active'))).scalar_one_or_none() or 0
    
    # recent uploads (last 7 days)
    recent_uploads = (
        await db.execute(
            select(func.count(Document.id)).where(Document.upload_date >= seven_days_ago)
        )
    ).scalar_one_or_none() or 0

    # 2. Charts
    monthly_sql = text("""
        SELECT to_char(invoice_date, 'YYYY-MM') as month,
               COALESCE(SUM(net_amount), 0) as revenue,
               COALESCE(SUM(CASE WHEN status = 'paid' THEN net_amount ELSE 0 END), 0) as paid,
               COALESCE(SUM(CASE WHEN status != 'paid' AND status != 'cancelled' THEN net_amount ELSE 0 END), 0) as pending
        FROM invoices WHERE EXTRACT(YEAR FROM invoice_date) = :year GROUP BY month ORDER BY month ASC
    """)
    monthly_trend = [
        MonthlyRevenueItem(month=r['month'], revenue=Decimal(str(r['revenue'])), paid=Decimal(str(r['paid'])), pending=Decimal(str(r['pending'])))
        for r in (await db.execute(monthly_sql, {"year": current_year})).mappings()
    ]

    invoice_status = [
        InvoiceStatusItem(name="Paid", value=paid_invoices),
        InvoiceStatusItem(name="Pending", value=pending_invoices)
    ]

    top_cust_sql = text("""
        SELECT c.customer_name, COALESCE(SUM(i.net_amount), 0) as revenue
        FROM invoices i JOIN customers c ON i.customer_id = c.id
        WHERE i.status != 'cancelled' GROUP BY c.id, c.customer_name ORDER BY revenue DESC LIMIT 5
    """)
    revenue_by_customer = [
        TopCustomerItem(customer_name=r['customer_name'], revenue=Decimal(str(r['revenue'])))
        for r in (await db.execute(top_cust_sql)).mappings()
    ]

    docs_sql = text("""
        SELECT to_char(upload_date, 'YYYY-MM') as month, COUNT(*) as count
        FROM documents WHERE is_deleted = false AND EXTRACT(YEAR FROM upload_date) = :year
        GROUP BY month ORDER BY month ASC
    """)
    documents_uploaded_per_month = [
        DocumentUploadItem(month=r['month'], count=r['count'])
        for r in (await db.execute(docs_sql, {"year": current_year})).mappings()
    ]

    recent_rev_sql = text("""
        SELECT to_char(invoice_date, 'YYYY-MM-DD') as date, COALESCE(SUM(net_amount), 0) as revenue
        FROM invoices WHERE invoice_date >= :start_date AND status != 'cancelled'
        GROUP BY date ORDER BY date ASC
    """)
    recent_revenue_trend = [
        RecentRevenueItem(date=r['date'], revenue=Decimal(str(r['revenue'])))
        for r in (await db.execute(recent_rev_sql, {"start_date": seven_days_ago})).mappings()
    ]

    return DashboardStatsResponse(
        monthly_revenue=monthly_rev, yearly_revenue=yearly_rev, total_customers=total_customers,
        total_documents=total_documents, total_invoices=total_invoices, paid_invoices=paid_invoices,
        pending_invoices=pending_invoices, outstanding_amount=outstanding_amount,
        active_loans=active_loans, recent_uploads=recent_uploads,
        revenue_trend=monthly_trend, invoice_status=invoice_status,
        revenue_by_customer=revenue_by_customer, documents_uploaded_per_month=documents_uploaded_per_month,
        recent_revenue_trend=recent_revenue_trend
    )

@router.get("/dashboard/activity", response_model=list[ActivityLogResponse])
async def get_dashboard_activity(
    current_user: User = Depends(RequireRole(["admin"])),
    db: AsyncSession = Depends(get_db)
):
    from sqlalchemy import desc
    stmt = (
        select(ActivityLog, User.full_name, User.email)
        .outerjoin(User, ActivityLog.user_id == User.id)
        .order_by(desc(ActivityLog.created_at))
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    activities = []
    for row in rows:
        log_obj = row[0]
        log_obj.user_name = row[1]
        log_obj.user_email = row[2]
        activities.append(log_obj)
        
    return activities
