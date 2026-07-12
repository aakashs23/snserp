"""Health, liveness, and readiness endpoints for production monitoring."""

import logging
import time

from fastapi import APIRouter
from sqlalchemy import text

from app.database.session import async_session_factory
from app.config.settings import settings
from app.services.storage_service import storage_list_buckets

router = APIRouter()
logger = logging.getLogger("snserp.health")


@router.get("/health")
async def health_check():
    """Basic health check – always returns 200 if the process is running."""
    return {
        "status": "healthy",
        "service": "Sri Naga Sai ERP Backend",
        "version": "1.0.0",
        "environment": settings.app_env,
    }


@router.get("/health/liveness")
async def liveness():
    """Kubernetes-style liveness probe – confirms the process is alive."""
    return {"status": "alive"}


@router.get("/health/readiness")
async def readiness():
    """Deep readiness check – verifies database, storage, and AI connectivity."""
    checks = {}
    overall = True

    # ── Database check ────────────────────────────────────────────────────
    try:
        start = time.perf_counter()
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        db_ms = (time.perf_counter() - start) * 1000
        checks["database"] = {"status": "ok", "latency_ms": round(db_ms, 1)}
    except Exception as e:
        # Raw exception text can include the DSN (with credentials) for some
        # connection-level driver errors. This endpoint is unauthenticated, so
        # only a generic message goes to the client; full detail is logged.
        logger.error("Readiness DB check failed: %s", e)
        checks["database"] = {"status": "error", "detail": "Database connection failed."}
        overall = False

    # ── Storage check (Supabase) ──────────────────────────────────────────
    try:
        start = time.perf_counter()
        await storage_list_buckets()
        storage_ms = (time.perf_counter() - start) * 1000
        checks["storage"] = {"status": "ok", "latency_ms": round(storage_ms, 1)}
    except Exception as e:
        logger.error("Readiness storage check failed: %s", e)
        checks["storage"] = {"status": "error", "detail": "Storage connection failed."}
        overall = False

    # ── AI provider check ────────────────────────────────────────────────
    try:
        from app.services.ai_service import get_primary_provider

        provider = get_primary_provider()
        if provider:
            start = time.perf_counter()
            available = await provider.is_available()
            ai_ms = (time.perf_counter() - start) * 1000
            if available:
                checks["ai_provider"] = {
                    "status": "ok",
                    "provider": provider.name,
                    "latency_ms": round(ai_ms, 1),
                }
            else:
                checks["ai_provider"] = {
                    "status": "degraded",
                    "provider": provider.name,
                    "detail": "Provider reported unavailable",
                }
        else:
            checks["ai_provider"] = {"status": "error", "detail": "No primary provider configured"}
            overall = False
    except Exception as e:
        # Some providers (e.g. Gemini's REST transport) embed the API key as a
        # query param; an SDK-level HTTP error could echo that URL in str(e).
        logger.error("Readiness AI provider check failed: %s", e)
        # AI being down is degraded, not a full failure
        checks["ai_provider"] = {"status": "degraded", "detail": "AI provider check failed."}

    status_code = 200 if overall else 503
    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if overall else "not_ready",
            "checks": checks,
        },
    )
