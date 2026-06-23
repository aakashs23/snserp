"""Sri Naga Sai ERP - FastAPI Backend Entry Point."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from app.config.settings import settings
from app.database.session import async_session_factory
from app.models.users import Role
from app.config.supabase import ensure_documents_bucket

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.customers import router as customers_router
from app.api.invoices import router as invoices_router
from app.api.documents import router as documents_router
from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router
from app.api.calculator import router as calculator_router
from app.api.activity import router as activity_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: seed default roles and ensure storage buckets on startup."""
    # Ensure Supabase storage buckets exist
    ensure_documents_bucket()
    
    async with async_session_factory() as session:
        count = await session.execute(select(func.count()).select_from(Role))
        if count.scalar_one() == 0:
            roles = [
                Role(id=uuid.uuid4(), name="admin", description="System Administrator"),
                Role(id=uuid.uuid4(), name="accountant", description="Accountant with financial access"),
                Role(id=uuid.uuid4(), name="employee", description="Employee with read-only revenue dashboard"),
                Role(id=uuid.uuid4(), name="viewer", description="Read-only viewer"),
            ]
            session.add_all(roles)
            await session.commit()
    yield


app = FastAPI(
    title="Sri Naga Sai ERP",
    description="AI-Powered ERP & Intelligent Document Management System for Solar Companies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(customers_router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(invoices_router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(calculator_router, prefix="/api/v1/calculator", tags=["Calculator"])
app.include_router(activity_router, prefix="/api/v1/activity", tags=["Activity Logs"])
