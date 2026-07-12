"""Auth API router — current user profile."""

import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.models.users import User
from app.schemas.users import UserResponse
from app.config.settings import settings

router = APIRouter()
logger = logging.getLogger("snserp.auth")

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


class TurnstileVerifyRequest(BaseModel):
    token: str


@router.post("/verify-turnstile")
async def verify_turnstile(payload: TurnstileVerifyRequest):
    """Verify a Cloudflare Turnstile token server-side against the official siteverify
    endpoint. The secret never leaves the backend."""
    if not settings.turnstile_secret_key:
        # Fail closed: an unconfigured secret must not silently allow requests through.
        logger.error("TURNSTILE_SECRET_KEY is not configured")
        raise HTTPException(status_code=500, detail="CAPTCHA verification is not configured.")

    if not payload.token:
        raise HTTPException(status_code=400, detail="Missing CAPTCHA token.")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                TURNSTILE_VERIFY_URL,
                data={"secret": settings.turnstile_secret_key, "response": payload.token},
            )
        result = resp.json()
    except Exception as e:
        logger.warning("Turnstile siteverify request failed: %s", e)
        raise HTTPException(status_code=502, detail="Could not reach CAPTCHA verification service.")

    if not result.get("success"):
        logger.warning("Turnstile verification rejected: %s", result.get("error-codes"))
        raise HTTPException(status_code=403, detail="CAPTCHA verification failed.")

    return {"success": True}


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

