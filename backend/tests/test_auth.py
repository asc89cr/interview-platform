"""Unit tests for JWT auth and subscription tier limit logic.

Run with:
    pytest backend/tests/test_auth.py -v
"""
import os

# Provide a parseable DATABASE_URL before any SQLAlchemy engine is initialised.
# The tests here never open a real connection; the engine is only created at
# module import time in backend.db.base.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost:5432/test_db")

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from jose import JWTError

# Isolate jwt module — no DB or Stripe needed
from backend.auth import jwt as jwt_utils
from backend.billing.limits import (
    TIER_LIMITS,
    check_analysis_allowed,
    check_interviewer_profile_limit,
    check_pdf_export_allowed,
    check_session_limit,
)

# ── Helpers ────────────────────────────────────────────────────────────────────

def _uid() -> str:
    return str(uuid.uuid4())


def _mock_user(tier: str) -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = tier
    return user


def _mock_db(session_count: int) -> AsyncMock:
    db = AsyncMock()
    scalar_result = MagicMock()
    scalar_result.scalar_one.return_value = session_count
    db.execute = AsyncMock(return_value=scalar_result)
    return db


# ── JWT: access token ──────────────────────────────────────────────────────────

class TestAccessToken:
    def test_roundtrip(self):
        uid = _uid()
        token = jwt_utils.create_access_token(uid)
        payload = jwt_utils.decode_access_token(token)
        assert payload["sub"] == uid
        assert payload["type"] == "access"

    def test_tampered_token_rejected(self):
        token = jwt_utils.create_access_token(_uid())
        with pytest.raises(JWTError):
            jwt_utils.decode_access_token(token[:-5] + "XXXXX")

    def test_refresh_token_rejected_as_access(self):
        refresh = jwt_utils.create_refresh_token(_uid())
        with pytest.raises(JWTError):
            jwt_utils.decode_access_token(refresh)


# ── JWT: refresh token rotation ────────────────────────────────────────────────

class TestRefreshToken:
    def test_rotation_issues_new_pair(self):
        uid = _uid()
        refresh = jwt_utils.create_refresh_token(uid)
        new_access, new_refresh = jwt_utils.rotate_refresh_token(refresh)

        payload = jwt_utils.decode_access_token(new_access)
        assert payload["sub"] == uid

        # New refresh is independently valid
        a2, _ = jwt_utils.rotate_refresh_token(new_refresh)
        assert jwt_utils.decode_access_token(a2)["sub"] == uid

    def test_old_refresh_revoked_after_rotation(self):
        uid = _uid()
        refresh = jwt_utils.create_refresh_token(uid)
        jwt_utils.rotate_refresh_token(refresh)

        with pytest.raises(JWTError):
            jwt_utils.rotate_refresh_token(refresh)

    def test_revoke_prevents_rotation(self):
        uid = _uid()
        refresh = jwt_utils.create_refresh_token(uid)
        jwt_utils.revoke_refresh_token(refresh)

        with pytest.raises(JWTError):
            jwt_utils.rotate_refresh_token(refresh)

    def test_access_token_rejected_as_refresh(self):
        access = jwt_utils.create_access_token(_uid())
        with pytest.raises(JWTError):
            jwt_utils.rotate_refresh_token(access)

    def test_revoke_unknown_token_is_silent(self):
        """Revoking a garbage / already-expired token must not raise."""
        jwt_utils.revoke_refresh_token("not.a.token")


# ── Tier limits structure ──────────────────────────────────────────────────────

class TestTierLimitsStructure:
    def test_all_tiers_present(self):
        for tier in ("free", "pro", "teams"):
            assert tier in TIER_LIMITS

    def test_free_sessions_capped(self):
        assert TIER_LIMITS["free"]["sessions_per_month"] == 3

    def test_pro_sessions_unlimited(self):
        assert TIER_LIMITS["pro"]["sessions_per_month"] is None

    def test_teams_pdf_export(self):
        assert TIER_LIMITS["teams"]["pdf_export"] is True

    def test_free_no_pdf_export(self):
        assert TIER_LIMITS["free"]["pdf_export"] is False


# ── check_session_limit ────────────────────────────────────────────────────────

class TestCheckSessionLimit:
    @pytest.mark.asyncio
    async def test_free_within_limit(self):
        await check_session_limit(_mock_user("free"), _mock_db(2))

    @pytest.mark.asyncio
    async def test_free_at_limit_raises(self):
        with pytest.raises(ValueError, match="Monthly session limit"):
            await check_session_limit(_mock_user("free"), _mock_db(3))

    @pytest.mark.asyncio
    async def test_free_over_limit_raises(self):
        with pytest.raises(ValueError):
            await check_session_limit(_mock_user("free"), _mock_db(10))

    @pytest.mark.asyncio
    async def test_pro_unlimited(self):
        # DB is never consulted for unlimited tiers
        db = AsyncMock()
        await check_session_limit(_mock_user("pro"), db)
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_teams_unlimited(self):
        db = AsyncMock()
        await check_session_limit(_mock_user("teams"), db)
        db.execute.assert_not_called()


# ── check_analysis_allowed ─────────────────────────────────────────────────────

class TestCheckAnalysisAllowed:
    @pytest.mark.asyncio
    async def test_free_blocked(self):
        with pytest.raises(ValueError, match="Free tier"):
            await check_analysis_allowed(_mock_user("free"))

    @pytest.mark.asyncio
    async def test_pro_allowed(self):
        await check_analysis_allowed(_mock_user("pro"))

    @pytest.mark.asyncio
    async def test_teams_allowed(self):
        await check_analysis_allowed(_mock_user("teams"))


# ── check_interviewer_profile_limit ───────────────────────────────────────────

class TestCheckInterviewerProfileLimit:
    def test_free_at_limit_raises(self):
        with pytest.raises(ValueError, match="Interviewer profile limit"):
            check_interviewer_profile_limit(_mock_user("free"), current_count=1)

    def test_free_below_limit_ok(self):
        check_interviewer_profile_limit(_mock_user("free"), current_count=0)

    def test_pro_unlimited(self):
        check_interviewer_profile_limit(_mock_user("pro"), current_count=999)

    def test_teams_unlimited(self):
        check_interviewer_profile_limit(_mock_user("teams"), current_count=500)


# ── check_pdf_export_allowed ───────────────────────────────────────────────────

class TestCheckPdfExportAllowed:
    def test_free_blocked(self):
        with pytest.raises(ValueError, match="Teams tier"):
            check_pdf_export_allowed(_mock_user("free"))

    def test_pro_blocked(self):
        with pytest.raises(ValueError, match="Teams tier"):
            check_pdf_export_allowed(_mock_user("pro"))

    def test_teams_allowed(self):
        check_pdf_export_allowed(_mock_user("teams"))
