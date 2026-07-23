from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.session import Session


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    # e.g. {"technical": 7.5, "behavioral": 8.0, "communication": 6.5}
    category_scores: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    strengths: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    weaknesses: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    interviewer_intent_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_practice: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    pdf_report_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    session: Mapped["Session"] = relationship("Session", back_populates="analysis_report")
