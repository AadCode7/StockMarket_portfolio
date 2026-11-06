from functools import lru_cache
from typing import Annotated, Any
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWTError
from app.config import settings
from app.schemas import UserContext

bearer = HTTPBearer(auto_error=False)

@lru_cache
def jwks_client() -> PyJWKClient:
    if not settings.supabase_jwks_url:
        raise RuntimeError("SUPABASE_JWKS_URL is not configured")
    return PyJWKClient(settings.supabase_jwks_url, cache_keys=True)

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> UserContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not settings.supabase_jwt_issuer or not settings.supabase_jwks_url:
        raise HTTPException(status_code=503, detail="Authentication is not configured")
    try:
        key = jwks_client().get_signing_key_from_jwt(credentials.credentials)
        claims: dict[str, Any] = jwt.decode(
            credentials.credentials, key.key, algorithms=["ES256", "RS256"],
            audience="authenticated", issuer=settings.supabase_jwt_issuer,
            options={"require": ["exp", "sub", "iss", "aud"]},
        )
        if not claims.get("sub"):
            raise PyJWTError("Missing subject")
        return UserContext(id=claims["sub"], email=claims.get("email"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
