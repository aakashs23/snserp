"""Sri Naga Sai ERP - FastAPI Backend Entry Point."""

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from sqlalchemy import func, select

from app.config.settings import settings
from app.database.session import async_session_factory
from app.models.users import Role
from app.config.supabase import ensure_documents_bucket
from app.middleware.compression import install_compression_exclusions
from app.middleware.logging import RequestLoggingMiddleware

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.customers import router as customers_router
from app.api.invoices import router as invoices_router
from app.api.documents import router as documents_router
from app.api.document_permissions import router as document_permissions_router
from app.api.analytics import router as analytics_router
from app.api.chat import router as chat_router
from app.api.calculator import router as calculator_router
from app.api.activity import router as activity_router
from app.api.loans import router as loans_router
from app.api.users import router as users_router
from app.api.notifications import router as notifications_router


from app.services.cleanup import delete_expired_trash_loop
import asyncio

# ─── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("snserp")

# ─── Rate limiter (shared across routers) ─────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: seed default roles and ensure storage buckets on startup."""
    # Fail closed outside development if critical secrets are missing.
    if settings.app_env != "development":
        missing = [
            name for name, value in (
                ("SUPABASE_URL", settings.supabase_url),
                ("SUPABASE_SERVICE_KEY", settings.supabase_service_key),
            ) if not value
        ]
        if missing:
            raise RuntimeError(
                f"Refusing to start in '{settings.app_env}': missing required secrets: "
                + ", ".join(missing)
            )
        if settings.jwt_secret == "dev-secret-change-in-production":
            logger.warning("JWT_SECRET is still the default value.")
        if "localhost" in settings.database_url:
            logger.warning("DATABASE_URL points at localhost outside development.")

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
            
    # Start background tasks
    cleanup_task = asyncio.create_task(delete_expired_trash_loop())
    
    logger.info("Sri Naga Sai ERP started successfully (env=%s)", settings.app_env)
    yield
    
    # Cancel background tasks on shutdown
    cleanup_task.cancel()



# Expose interactive API docs only in development — they map the full API surface.
_docs_enabled = settings.app_env == "development"

app = FastAPI(
    title="Sri Naga Sai ERP",
    description="AI-Powered ERP & Intelligent Document Management System for Solar Companies",
    version="1.0.0",
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
    lifespan=lifespan,
)

# ─── Attach rate limiter to app ───────────────────────────────────────────────
async def _log_and_handle_rate_limit(request: Request, exc: RateLimitExceeded):
    """Log throttled requests (unusual-traffic signal), then use slowapi's handler."""
    client_ip = request.client.host if request.client else "unknown"
    logger.warning(
        "rate_limit_exceeded | ip=%s method=%s path=%s",
        client_ip, request.method, request.url.path,
    )
    return _rate_limit_exceeded_handler(request, exc)


app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _log_and_handle_rate_limit)


# ─── Security headers ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Baseline hardening headers. HSTS is ignored by browsers over plain HTTP,
    so it is safe to send in every environment; TLS termination is done upstream."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    # This API only ever serves JSON — no HTML, scripts, or embeds. A locked-down
    # CSP here is safe (the UI is a separate Next.js origin with its own policy).
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# ─── Request logging middleware ───────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ─── Response compression ─────────────────────────────────────────────────────
# Added after RequestLogging and before CORS, so it sits inside the CORS layer.
install_compression_exclusions()
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=6)

# ─── Global rate limiting ─────────────────────────────────────────────────────
# Without this middleware slowapi's default_limits never fire, leaving every
# endpoint without an explicit @limiter.limit unthrottled. Added inside CORS so
# 429 responses still carry CORS headers. Stricter per-route limits still win.
app.add_middleware(SlowAPIMiddleware)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ─── HTTPS redirect ────────────────────────────────────────────────────────────
# Added last so it becomes the outermost middleware layer, running before CORS,
# rate limiting, and everything else — a plain-HTTP request never reaches them.
# TLS terminates upstream (see add_security_headers above), so request.url.scheme
# is always 'http' internally even for a visitor on https; x-forwarded-proto is
# what the edge actually saw. A proxy chain can send a comma-separated list
# ("https, http"); the client-facing hop is always the first entry.
@app.middleware("http")
async def redirect_http_to_https(request: Request, call_next):
    if settings.app_env != "development":
        forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
        if forwarded_proto == "http":
            https_url = request.url.replace(scheme="https")
            # 308: preserves the method, so a POST isn't downgraded to GET on retry.
            # replace() carries the full path and query string over unchanged.
            return RedirectResponse(url=str(https_url), status_code=308)
    return await call_next(request)

# ─── Global exception handlers ───────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a standardised JSON response."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled exception | request_id=%s", request_id)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "request_id": request_id,
        },
        headers={"X-Request-ID": request_id},
    )


# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(health_router, tags=["Health"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(customers_router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(invoices_router, prefix="/api/v1/invoices", tags=["Invoices"])
app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(document_permissions_router, prefix="/api/v1/documents", tags=["Document Permissions"])
app.include_router(analytics_router, prefix="/api/v1/analytics", tags=["Analytics"])
app.include_router(chat_router, prefix="/api/v1/chat", tags=["AI Chat"])
app.include_router(calculator_router, prefix="/api/v1/calculator", tags=["Calculator"])
app.include_router(activity_router, prefix="/api/v1/activity", tags=["Activity Logs"])
app.include_router(loans_router, prefix="/api/v1/loans", tags=["Loans"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(notifications_router, prefix="/api/v1/notifications", tags=["Notifications"])
