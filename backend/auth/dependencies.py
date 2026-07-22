"""FastAPI dependency that authenticates every protected route.

Usage in any router:
    from backend.auth.dependencies import get_current_user

    @router.get("/me")
    async def me(user: User = Depends(get_current_user)):
        ...
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import decode_access_token
from backend.db.base import get_db
from backend.db.models.user import User

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate the Bearer JWT and return the authenticated User ORM object."""
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str: str = payload["sub"]
        user_id = uuid.UUID(user_id_str)
    except (JWTError, KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user: User | None = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
