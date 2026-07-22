"""
Seed script for local development.

Usage:
    python -m backend.seeds.seed

Creates:
  - 1 sample user  (dev@example.com / password: devpassword)
  - 1 candidate profile
  - 1 interviewer profile
  - 1 interview session
"""
import asyncio
import hashlib
import uuid
from datetime import datetime, timezone

from backend.db.base import AsyncSessionLocal
from backend.db.models import (
    AnalysisReport,
    AttachedFile,
    CandidateProfile,
    InterviewerProfile,
    Session,
    Turn,
    User,
)


def _fake_hash(password: str) -> str:
    """Placeholder hash — replace with bcrypt in Auth Agent."""
    return "sha256:" + hashlib.sha256(password.encode()).hexdigest()


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        # Check if seed data already exists
        from sqlalchemy import select

        existing = await db.execute(select(User).where(User.email == "dev@example.com"))
        if existing.scalar_one_or_none():
            print("Seed data already present — skipping.")
            return

        # ── User ──────────────────────────────────────────────────────────────
        user = User(
            id=uuid.uuid4(),
            email="dev@example.com",
            password_hash=_fake_hash("devpassword"),
            name="Dev User",
            subscription_tier="pro",
        )
        db.add(user)
        await db.flush()  # get user.id

        # ── Candidate Profile ─────────────────────────────────────────────────
        profile = CandidateProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            target_role="Senior Software Engineer",
            target_salary_usd=150_000,
            skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
            weak_areas=["System Design at scale", "Negotiation"],
            custom_notes="Applying to FAANG-tier companies. Focus on behavioral.",
        )
        db.add(profile)

        # ── Interviewer Profile ───────────────────────────────────────────────
        interviewer = InterviewerProfile(
            id=uuid.uuid4(),
            user_id=user.id,
            name="Jane Smith",
            company="Acme Corp",
            role="Engineering Manager",
            interview_style="behavioral",
            known_questions=[
                "Tell me about a time you disagreed with your manager.",
                "Describe a project where you had to meet a tight deadline.",
            ],
            notes="Known for deep dives into team conflict resolution.",
        )
        db.add(interviewer)
        await db.flush()

        # ── Interview Session ─────────────────────────────────────────────────
        session = Session(
            id=uuid.uuid4(),
            user_id=user.id,
            candidate_profile_id=profile.id,
            interviewer_profile_id=interviewer.id,
            status="analysed",
            started_at=datetime(2026, 7, 1, 10, 0, tzinfo=timezone.utc),
            ended_at=datetime(2026, 7, 1, 11, 0, tzinfo=timezone.utc),
        )
        db.add(session)
        await db.flush()

        # ── Attached File ─────────────────────────────────────────────────────
        db.add(AttachedFile(
            id=uuid.uuid4(),
            session_id=session.id,
            label="Job Description",
            file_url="https://s3.example.com/files/jd-acme.pdf",
            file_type="application/pdf",
        ))

        # ── Turns ─────────────────────────────────────────────────────────────
        db.add(Turn(
            id=uuid.uuid4(),
            session_id=session.id,
            speaker="Interviewer",
            text="Tell me about a time you disagreed with your manager.",
            timestamp=datetime(2026, 7, 1, 10, 5, tzinfo=timezone.utc),
        ))
        db.add(Turn(
            id=uuid.uuid4(),
            session_id=session.id,
            speaker="Candidate",
            text="Sure. At my last job we disagreed on sprint scope...",
            generated_answer=(
                "Start with the situation: briefly describe the disagreement. "
                "Then focus on how you listened first, then presented data to support your view."
            ),
            timestamp=datetime(2026, 7, 1, 10, 6, tzinfo=timezone.utc),
        ))

        # ── Analysis Report ───────────────────────────────────────────────────
        db.add(AnalysisReport(
            id=uuid.uuid4(),
            session_id=session.id,
            overall_score=7.8,
            category_scores={"technical": 7.0, "behavioral": 8.5, "communication": 7.5},
            strengths=["Clear structure", "Good use of STAR method"],
            weaknesses=["Could quantify impact more", "Slight filler word overuse"],
            interviewer_intent_summary=(
                "Jane was probing for conflict-resolution maturity and self-awareness."
            ),
            recommended_practice=[
                "Practice quantifying outcomes (reduced latency by X%)",
                "Mock behavioral questions with 90-second time limit",
            ],
        ))

        await db.commit()
        print(f"✅  Seed complete. User: dev@example.com | Session ID: {session.id}")


if __name__ == "__main__":
    asyncio.run(seed())
