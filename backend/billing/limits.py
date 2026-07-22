"""Subscription tier limits and enforcement helpers.

Call these from any protected endpoint before allowing the action:

    await check_session_limit(user, db)       # raises ValueError if over limit
    await check_analysis_allowed(user)         # raises ValueError if tier blocks it
    check_interviewer_profile_limit(user, n)   # raises ValueError if at cap
"""
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models.session import Session
from backend.db.models.user import User

TIER_LIMITS: dict[str, dict] = {
    "free": {
        "sessions_per_month": 3,
        "analysis_reports": False,
        "interviewer_profiles": 1,
        "pdf_export": False,
        "team_members": None,
    },
    "pro": {
        "sessions_per_month": None,   # unlimited
        "analysis_reports": True,
        "interviewer_profiles": None,  # unlimited
        "pdf_export": False,
        "team_members": None,
    },
    "teams": {
        "sessions_per_month": None,
        "analysis_reports": True,
        "interviewer_profiles": None,
        "pdf_export": True,
        "team_members": 10,
    },
}


def _limits(user: User) -> dict:
    return TIER_LIMITS.get(user.subscription_tier, TIER_LIMITS["free"])


async def check_session_limit(user: User, db: AsyncSession) -> None:
    """Raise ValueError when the user has reached their monthly session cap."""
    limit: int | None = _limits(user)["sessions_per_month"]
    if limit is None:
        return  # unlimited

    month_start = datetime.now(timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    result = await db.execute(
        select(func.count()).select_from(Session).where(
            Session.user_id == user.id,
            Session.created_at >= month_start,
        )
    )
    count: int = result.scalar_one()
    if count >= limit:
        raise ValueError(
            f"Monthly session limit reached ({limit} sessions). "
            "Upgrade to Pro for unlimited sessions."
        )


async def check_analysis_allowed(user: User) -> None:
    """Raise ValueError when the user's tier does not include analysis reports."""
    if not _limits(user)["analysis_reports"]:
        raise ValueError(
            "Analysis reports are not available on the Free tier. "
            "Upgrade to Pro or Teams to access this feature."
        )


def check_interviewer_profile_limit(user: User, current_count: int) -> None:
    """Raise ValueError when the user has reached their interviewer profile cap."""
    limit: int | None = _limits(user)["interviewer_profiles"]
    if limit is None:
        return  # unlimited
    if current_count >= limit:
        raise ValueError(
            f"Interviewer profile limit reached ({limit} profile(s)). "
            "Upgrade to Pro for unlimited profiles."
        )


def check_pdf_export_allowed(user: User) -> None:
    """Raise ValueError when the user's tier does not include PDF export."""
    if not _limits(user).get("pdf_export", False):
        raise ValueError(
            "PDF export is only available on the Teams tier."
        )
