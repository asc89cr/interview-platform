"""
Unit tests for Pydantic v2 schemas.
Run with: pytest backend/tests/test_schemas.py -v
"""
import uuid
from datetime import datetime, timezone

import pytest

from backend.schemas.analysis import AnalysisReportCreate, AnalysisReportRead, CategoryScores
from backend.schemas.session import (
    CandidateProfileCreate,
    CandidateProfileRead,
    InterviewerProfileCreate,
    InterviewerProfileRead,
    SessionCreate,
    SessionRead,
    SessionReadDetail,
    TurnCreate,
    TurnRead,
)
from backend.schemas.user import UserCreate, UserRead, UserUpdate


# ── Helpers ───────────────────────────────────────────────────────────────────

_NOW = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
_UUID = uuid.uuid4()


# ── User schemas ──────────────────────────────────────────────────────────────

class TestUserCreate:
    def test_valid(self):
        u = UserCreate(email="alice@example.com", password="secret123", name="Alice")
        assert u.email == "alice@example.com"

    def test_invalid_email(self):
        with pytest.raises(Exception):
            UserCreate(email="not-an-email", password="x", name="X")

    def test_missing_required(self):
        with pytest.raises(Exception):
            UserCreate(email="a@b.com", name="A")  # missing password


class TestUserRead:
    def test_from_dict(self):
        data = dict(id=_UUID, email="a@b.com", name="A", subscription_tier="free", created_at=_NOW)
        r = UserRead(**data)
        assert r.subscription_tier == "free"

    def test_from_attributes(self):
        class FakeOrm:
            id = _UUID
            email = "a@b.com"
            name = "Alice"
            subscription_tier = "pro"
            created_at = _NOW
        r = UserRead.model_validate(FakeOrm())
        assert r.name == "Alice"


class TestUserUpdate:
    def test_all_optional(self):
        u = UserUpdate()
        assert u.name is None and u.email is None

    def test_partial(self):
        u = UserUpdate(name="Bob")
        assert u.name == "Bob"


# ── Candidate profile schemas ─────────────────────────────────────────────────

class TestCandidateProfileCreate:
    def test_defaults(self):
        c = CandidateProfileCreate()
        assert c.skills == []
        assert c.weak_areas == []

    def test_full(self):
        c = CandidateProfileCreate(
            target_role="SWE",
            target_salary_usd=120_000,
            skills=["Python"],
            weak_areas=["System Design"],
        )
        assert c.target_salary_usd == 120_000


class TestCandidateProfileRead:
    def test_from_orm(self):
        class Orm:
            id = _UUID
            user_id = _UUID
            resume_url = None
            parsed_resume = None
            target_role = "SWE"
            target_salary_usd = None
            skills = ["Python"]
            weak_areas = []
            custom_notes = None
            updated_at = _NOW
        r = CandidateProfileRead.model_validate(Orm())
        assert r.target_role == "SWE"


# ── Interviewer profile schemas ───────────────────────────────────────────────

class TestInterviewerProfileCreate:
    def test_valid(self):
        p = InterviewerProfileCreate(name="Jane", interview_style="behavioral")
        assert p.known_questions == []

    def test_invalid_missing_name(self):
        with pytest.raises(Exception):
            InterviewerProfileCreate()


class TestInterviewerProfileRead:
    def test_from_orm(self):
        class Orm:
            id = _UUID
            user_id = _UUID
            name = "Jane"
            company = "Acme"
            role = "EM"
            interview_style = "behavioral"
            known_questions = ["Tell me about yourself"]
            notes = None
            created_at = _NOW
        r = InterviewerProfileRead.model_validate(Orm())
        assert r.company == "Acme"


# ── Session schemas ───────────────────────────────────────────────────────────

class TestSessionCreate:
    def test_all_optional(self):
        s = SessionCreate()
        assert s.candidate_profile_id is None

    def test_with_ids(self):
        s = SessionCreate(candidate_profile_id=_UUID, interviewer_profile_id=_UUID)
        assert s.candidate_profile_id == _UUID


class TestSessionRead:
    def test_from_orm(self):
        class Orm:
            id = _UUID
            user_id = _UUID
            candidate_profile_id = None
            interviewer_profile_id = None
            status = "active"
            started_at = None
            ended_at = None
            created_at = _NOW
        r = SessionRead.model_validate(Orm())
        assert r.status == "active"


class TestSessionReadDetail:
    def test_empty_relations(self):
        class Orm:
            id = _UUID
            user_id = _UUID
            candidate_profile_id = None
            interviewer_profile_id = None
            status = "active"
            started_at = None
            ended_at = None
            created_at = _NOW
            attached_files = []
            turns = []
        r = SessionReadDetail.model_validate(Orm())
        assert r.turns == []


# ── Turn schemas ──────────────────────────────────────────────────────────────

class TestTurnCreate:
    def test_valid(self):
        t = TurnCreate(speaker="Interviewer", text="Tell me about yourself.")
        assert t.audio_url is None

    def test_missing_required(self):
        with pytest.raises(Exception):
            TurnCreate(speaker="Interviewer")  # missing text


# ── Analysis report schemas ───────────────────────────────────────────────────

class TestCategoryScores:
    def test_valid_range(self):
        c = CategoryScores(technical=7.5, behavioral=8.0, communication=6.0)
        assert c.technical == 7.5

    def test_out_of_range(self):
        with pytest.raises(Exception):
            CategoryScores(technical=11.0)


class TestAnalysisReportCreate:
    def test_defaults(self):
        a = AnalysisReportCreate()
        assert a.strengths == []
        assert a.overall_score is None

    def test_with_scores(self):
        a = AnalysisReportCreate(
            overall_score=8.0,
            category_scores=CategoryScores(technical=8.0),
            strengths=["Clear answers"],
        )
        assert a.overall_score == 8.0


class TestAnalysisReportRead:
    def test_from_orm(self):
        class Orm:
            id = _UUID
            session_id = _UUID
            overall_score = 7.5
            category_scores = {"technical": 7.5}
            strengths = ["Good structure"]
            weaknesses = ["Too verbose"]
            interviewer_intent_summary = "Testing depth"
            recommended_practice = ["Practice STAR"]
            pdf_report_url = None
            generated_at = _NOW
        r = AnalysisReportRead.model_validate(Orm())
        assert r.overall_score == 7.5
        assert "Good structure" in r.strengths
