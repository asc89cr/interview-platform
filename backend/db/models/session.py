from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.analysis_report import AnalysisReport
    from backend.db.models.attached_file import AttachedFile
    from backend.db.models.candidate_profile import CandidateProfile
    from backend.db.models.interviewer_profile import InterviewerProfile
    from backend.db.models.turn import Turn
    from backend.db.models.user import User


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    candidate_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("candidate_profiles.id", ondelete="SET NULL"), nullable=True
    )
    interviewer_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("interviewer_profiles.id", ondelete="SET NULL"), nullable=True
    )
    # Values: active | completed | analysing | analysed
    status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="active")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="sessions")
    candidate_profile: Mapped["CandidateProfile"] = relationship("CandidateProfile")
    interviewer_profile: Mapped["InterviewerProfile"] = relationship(
        "InterviewerProfile", back_populates="sessions"
    )
    attached_files: Mapped[list["AttachedFile"]] = relationship(
        "AttachedFile", back_populates="session", cascade="all, delete-orphan"
    )
    turns: Mapped[list["Turn"]] = relationship(
        "Turn", back_populates="session", cascade="all, delete-orphan", order_by="Turn.timestamp"
    )
    analysis_report: Mapped["AnalysisReport"] = relationship(
        "AnalysisReport", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
