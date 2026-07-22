"""Analysis report endpoints."""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.dependencies import get_current_user
from backend.billing.limits import check_analysis_allowed, check_pdf_export_allowed
from backend.db.base import get_db
from backend.db.models.analysis_report import AnalysisReport
from backend.db.models.session import Session
from backend.db.models.user import User
from backend.schemas.analysis import AnalysisReportRead
from backend.services.s3 import generate_presigned_download_url

router = APIRouter(tags=["reports"])


async def _get_owned_report(
    session_id: uuid.UUID, user: User, db: AsyncSession
) -> AnalysisReport:
    """Return the AnalysisReport for a session the user owns, or raise 404."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    result = await db.execute(
        select(AnalysisReport).where(AnalysisReport.session_id == session_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis report is not ready yet",
        )
    return report


@router.get("/sessions/{session_id}/report", response_model=AnalysisReportRead)
async def get_report(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the analysis report for a session (Pro/Teams tier required)."""
    try:
        await check_analysis_allowed(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    return await _get_owned_report(session_id, user, db)


@router.get("/sessions/{session_id}/report/pdf")
async def get_report_pdf(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Redirect to a presigned S3 PDF download URL (Teams tier required)."""
    try:
        check_pdf_export_allowed(user)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    report = await _get_owned_report(session_id, user, db)
    if not report.pdf_report_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF has not been generated for this report",
        )

    # Extract the S3 object key from the stored URL and issue a fresh signed URL
    key = report.pdf_report_url.split(".amazonaws.com/", 1)[-1]
    download_url = generate_presigned_download_url(key)
    return RedirectResponse(url=download_url, status_code=status.HTTP_302_FOUND)
