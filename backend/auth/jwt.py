"""JWT token creation, decoding, and rotation.

Access tokens expire in 15 minutes (HS256).
Refresh tokens expire in 30 days and are tracked server-side by JTI so they
can be individually revoked (logout, rotation).

NOTE: _valid_refresh_jtis is an in-process dict — suitable for a single-instance
deployment. Swap for Redis or a DB table when scaling horizontally.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt

SECRET_KEY: str = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 30

# {jti: user_id_str} — tracks valid refresh tokens
_valid_refresh_jtis: dict[str, str] = {}


def create_access_token(user_id: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    _valid_refresh_jtis[jti] = user_id
    return token


def decode_access_token(token: str) -> dict:
    """Decode and validate an access token. Raises JWTError on any failure."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Token is not an access token")
    return payload


def rotate_refresh_token(token: str) -> tuple[str, str]:
    """Validate a refresh token, revoke it, and issue a fresh access + refresh pair."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "refresh":
        raise JWTError("Token is not a refresh token")
    jti: str = payload.get("jti", "")
    user_id: str = payload.get("sub", "")
    if jti not in _valid_refresh_jtis:
        raise JWTError("Refresh token has been revoked or is unknown")
    del _valid_refresh_jtis[jti]
    return create_access_token(user_id), create_refresh_token(user_id)


def revoke_refresh_token(token: str) -> None:
    """Revoke a refresh token (used on logout). Silent if already invalid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti", "")
        _valid_refresh_jtis.pop(jti, None)
    except JWTError:
        pass
