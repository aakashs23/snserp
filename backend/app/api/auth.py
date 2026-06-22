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
