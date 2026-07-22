"""Auth endpoints: /auth/register, /auth/login, /auth/refresh, /auth/logout."""
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import jwt as jwt_utils
from backend.db.base import get_db
from backend.db.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Pydantic schemas (local to this router) ────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenBody(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account and receive access + refresh tokens",
)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        id=uuid.uuid4(),
        email=body.email,
        password_hash=_pwd.hash(body.password),
        name=body.name,
    )
    db.add(user)
    await db.flush()

    uid = str(user.id)
    return TokenResponse(
        access_token=jwt_utils.create_access_token(uid),
        refresh_token=jwt_utils.create_refresh_token(uid),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with email + password and receive tokens",
)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == body.email))
    user: User | None = result.scalar_one_or_none()

    if not user or not _pwd.verify(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    uid = str(user.id)
    return TokenResponse(
        access_token=jwt_utils.create_access_token(uid),
        refresh_token=jwt_utils.create_refresh_token(uid),
    )


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Exchange a valid refresh token for a new access + refresh token pair",
)
async def refresh(body: TokenBody) -> AccessTokenResponse:
    try:
        access_token, new_refresh = jwt_utils.rotate_refresh_token(body.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return AccessTokenResponse(access_token=access_token, refresh_token=new_refresh)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke the refresh token (client should discard both tokens)",
)
async def logout(body: TokenBody) -> None:
    jwt_utils.revoke_refresh_token(body.refresh_token)
