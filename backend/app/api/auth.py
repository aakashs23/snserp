"""Auth API router — current user profile."""

from fastapi import APIRouter, Depends

from app.middleware.auth import get_current_user
from app.models.users import User
from app.schemas.users import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user's profile."""
    return current_user

from app.services.activity_service import log_activity
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db

@router.post("/log-login")
async def log_login(
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
async def log_logout(
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
