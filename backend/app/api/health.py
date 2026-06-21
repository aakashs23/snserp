"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return application health status."""
    return {
        "status": "healthy",
        "service": "Sri Naga Sai ERP Backend",
        "version": "1.0.0",
    }
