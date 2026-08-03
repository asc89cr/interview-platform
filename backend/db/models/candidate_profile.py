from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base

if TYPE_CHECKING:
    from backend.db.models.user import User


class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    resume_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    parsed_resume: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    target_salary_usd: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    weak_areas: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    custom_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped[User] = relationship("User", back_populates="candidate_profile")
