"""Profile management endpoints.

Candidate profiles are 1-to-1 with each user and are created lazily on first
access.  Interviewer profiles are N-per-user and subject to tier limits.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.billing.limits import check_interviewer_profile_limit
from backend.db.base import get_db
from backend.db.models.candidate_profile import CandidateProfile
from backend.db.models.interviewer_profile import InterviewerProfile
from backend.db.models.user import User
from backend.schemas.session import (
    CandidateProfileRead,
    CandidateProfileUpdate,
    InterviewerProfileCreate,
    InterviewerProfileRead,
    InterviewerProfileUpdate,
)
from backend.services.s3 import generate_presigned_upload_url, make_resume_key

router = APIRouter(prefix="/profile", tags=["profiles"])


# ── Candidate profile ──────────────────────────────────────────────────────────

@router.get("/candidate", response_model=CandidateProfileRead)
async def get_candidate_profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's candidate profile, creating a blank one if absent."""
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)
        await db.flush()
    return profile


@router.put("/candidate", response_model=CandidateProfileRead)
async def update_candidate_profile(
    body: CandidateProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = CandidateProfile(user_id=user.id)
        db.add(profile)

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.flush()
    return profile


@router.post("/candidate/resume", status_code=status.HTTP_200_OK)
async def get_resume_upload_url(
    user: User = Depends(get_current_user),
):
    """Return a presigned S3 POST payload for uploading a resume PDF."""
    key = make_resume_key(str(user.id))
    return generate_presigned_upload_url(key, content_type="application/pdf")


# ── Interviewer profiles ───────────────────────────────────────────────────────

@router.get("/interviewers", response_model=list[InterviewerProfileRead])
async def list_interviewer_profiles(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterviewerProfile)
        .where(InterviewerProfile.user_id == user.id)
        .order_by(InterviewerProfile.created_at.desc())
    )
    return result.scalars().all()


@router.post(
    "/interviewers",
    response_model=InterviewerProfileRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_interviewer_profile(
    body: InterviewerProfileCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(InterviewerProfile).where(InterviewerProfile.user_id == user.id)
    )
    current_count = len(result.scalars().all())

    try:
        check_interviewer_profile_limit(user, current_count)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    profile = InterviewerProfile(user_id=user.id, **body.model_dump())
    db.add(profile)
    await db.flush()
    return profile


@router.put("/interviewers/{interviewer_id}", response_model=InterviewerProfileRead)
async def update_interviewer_profile(
    interviewer_id: uuid.UUID,
    body: InterviewerProfileUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(InterviewerProfile, interviewer_id)
    if profile is None or profile.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interviewer profile not found",
        )

    for field, value in body.model_dump(exclude_none=True).items():
        setattr(profile, field, value)

    await db.flush()
    return profile


@router.delete("/interviewers/{interviewer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interviewer_profile(
    interviewer_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await db.get(InterviewerProfile, interviewer_id)
    if profile is None or profile.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interviewer profile not found",
        )
    await db.delete(profile)
