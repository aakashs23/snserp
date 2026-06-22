from typing import List, Callable
from fastapi import Depends, HTTPException, status

from app.models.users import User
from app.middleware.auth import get_current_user

class RequireRole:
    """
    FastAPI dependency to require a specific role.
    Usage:
        @router.get("/admin", dependencies=[Depends(RequireRole(["admin"]))])
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if not user.role or user.role.name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the necessary permissions",
            )
        return user
