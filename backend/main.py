"""Sri Naga Sai ERP - FastAPI Backend Entry Point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.api.health import router as health_router

app = FastAPI(
    title="Sri Naga Sai ERP",
    description="AI-Powered ERP & Intelligent Document Management System for Solar Companies",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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


@app.on_event("startup")
async def startup_event():
    """Application startup tasks."""
    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks."""
    pass
