"""Auth API router — current user profile."""

from fastapi import APIRouter, Depends, Request

from app.middleware.auth import get_current_user
from app.models.users import User
from app.schemas.users import UserResponse
from app.config.settings import settings

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return current_user

from app.services.activity_service import log_activity
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/log-login")
@limiter.limit(settings.rate_limit_auth)
async def log_login(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await log_activity(
        db=db,
        user_id=current_user.id,
        action="Login",
        module="Auth",
        object_affected="System"
    )
    await db.commit()
    return {"message": "Logged"}

@router.post("/log-logout")
@limiter.limit(settings.rate_limit_auth)
async def log_logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    await log_activity(
        db=db,
        user_id=current_user.id,
        action="Logout",
        module="Auth",
        object_affected="System"
    )
    await db.commit()
    return {"message": "Logged"}

