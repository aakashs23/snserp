import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database.session import get_db
from app.auth.supabase_jwt import validate_supabase_jwt
from app.models.users import User

security = HTTPBearer()
logger = logging.getLogger("snserp.auth")


def _log_auth_failure(request: Request, reason: str) -> None:
    """Record a rejected authentication attempt for intrusion detection."""
    client_ip = request.client.host if request.client else "unknown"
    logger.warning("auth_failure | ip=%s path=%s reason=%s", client_ip, request.url.path, reason)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Validates the bearer token and returns the current user.
    If the user does not exist in the database (e.g. first login), 
    we could theoretically create them here, or rely on a webhook.
    For now, we expect them to exist.
    """
    token = credentials.credentials
    try:
        payload = validate_supabase_jwt(token)
    except ValueError as e:
        _log_auth_failure(request, "invalid_token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Supabase user ID is returned as the 'sub' field
    user_id_str = payload.get("sub")
    if not user_id_str:
        _log_auth_failure(request, "missing_sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing 'sub' claim",
        )

    # Fetch user from DB, join Role
    stmt = select(User).options(selectinload(User.role)).where(User.id == user_id_str)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        _log_auth_failure(request, "user_not_in_db")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in local database",
        )

    if not user.is_active:
        _log_auth_failure(request, "inactive_user")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return user

def require_roles(allowed_roles: list[str]):
    """
    Dependency factory to enforce role-based access control.
    Example: Depends(require_roles(["admin", "accountant"]))
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.role or current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user
    return role_checker
