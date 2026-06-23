from typing import Dict, Any

from app.config.supabase import supabase


def validate_supabase_jwt(token: str) -> Dict[str, Any]:
    """Validate a Supabase access token via the Supabase Auth API."""
    try:
        user_response = supabase.auth.get_user(jwt=token)
    except Exception as e:
        raise ValueError("Invalid token") from e

    if not user_response or not getattr(user_response, "user", None):
        raise ValueError("Invalid token")

    return {
        "sub": user_response.user.id,
        "email": user_response.user.email,
    }
