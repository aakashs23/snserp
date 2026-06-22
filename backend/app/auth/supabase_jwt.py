import jwt
from typing import Dict, Any

from app.config.settings import settings

def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a Supabase JWT.
    Since Supabase uses HS256 by default with the JWT_SECRET, we decode it using PyJWT.
    """
    try:
        # Supabase audience is usually 'authenticated'
        decoded = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False} # Sometimes audience varies, we disable strictly checking here for simplicity
        )
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
