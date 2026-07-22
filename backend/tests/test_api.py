"""Integration tests for all REST API endpoints (Agent 03).

All external dependencies (DB, S3, Redis) are mocked so no live services
are required.  Tests exercise routing, authorization checks, status codes,
and response shapes.

Run with:
    pytest backend/tests/test_api.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost:5432/test_db")

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app
from backend.auth.dependencies import get_current_user
from backend.db.base import get_db


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _make_user(tier: str = "pro") -> MagicMock:
    user = MagicMock()
    user.id = uuid.uuid4()
    user.subscription_tier = tier
    return user


def _make_db() -> AsyncMock:
    db = AsyncMock()
    db.flush = AsyncMock()
    db.delete = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _scalar_result(obj):
    result = MagicMock()
    result.scalar_one_or_none.return_value = obj
    result.scalars.return_value.all.return_value = [obj] if obj else []
    return result


def _override(user=None, db=None):
    """Return dependency overrides for the FastAPI app."""
    _user = user or _make_user()
    _db = db or _make_db()
    return {
        get_current_user: lambda: _user,
        get_db: lambda: _db,
    }


@pytest.fixture
def user():
    return _make_user()


@pytest.fixture
def db():
    return _make_db()


@pytest.fixture
def client(user, db):
    app.dependency_overrides = {
        get_current_user: lambda: user,
        get_db: lambda: _db_ctx(db),
    }
    transport = ASGITransport(app=app)
    c = AsyncClient(transport=transport, base_url="http://test")
    return c, user, db


async def _db_ctx(db):
    yield db


# ── Health check ───────────────────────────────────────────────────────────────

class TestHealth:
    @pytest.mark.asyncio
    async def test_health_ok(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


# ── Candidate profile ─────────────────────────────────────────────────────────

class TestCandidateProfile:
    @pytest.mark.asyncio
    async def test_get_creates_profile_if_missing(self):
        """When no profile exists, the route creates one and returns 200."""
        user = _make_user()
        db = AsyncMock()

        no_profile_result = MagicMock()
        no_profile_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=no_profile_result)

        # When db.add is called with the new CandidateProfile, populate server defaults
        def _add_side_effect(obj):
            from backend.db.models.candidate_profile import CandidateProfile as CP
            if isinstance(obj, CP):
                obj.id = uuid.uuid4()
                if obj.skills is None:
                    obj.skills = []
                if obj.weak_areas is None:
                    obj.weak_areas = []
                obj.updated_at = datetime.now(timezone.utc)

        db.add = MagicMock(side_effect=_add_side_effect)
        db.flush = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/profile/candidate", headers={"Authorization": "Bearer tok"})
        assert resp.status_code == 200
        db.add.assert_called_once()
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_get_returns_existing_profile(self):
        user = _make_user()
        profile = _make_candidate_profile(user.id)
        db = _mock_db_with_profile(profile)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/profile/candidate", headers={"Authorization": "Bearer tok"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == str(user.id)
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_update_candidate_profile(self):
        user = _make_user()
        profile = _make_candidate_profile(user.id)
        db = _mock_db_with_profile(profile)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.put(
                "/profile/candidate",
                json={"target_role": "Senior Engineer", "skills": ["Python", "Go"]},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 200
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_resume_upload_url_calls_s3(self):
        user = _make_user()

        with patch("backend.routers.profiles.generate_presigned_upload_url") as mock_s3:
            mock_s3.return_value = {"url": "https://s3.example.com", "fields": {}, "key": "k"}

            app.dependency_overrides = {get_current_user: lambda: user}
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    "/profile/candidate/resume",
                    headers={"Authorization": "Bearer tok"},
                )
            assert resp.status_code == 200
            assert "url" in resp.json()
            mock_s3.assert_called_once()
        app.dependency_overrides = {}


# ── Interviewer profiles ───────────────────────────────────────────────────────

class TestInterviewerProfiles:
    @pytest.mark.asyncio
    async def test_list_returns_profiles(self):
        user = _make_user()
        ip = _make_interviewer_profile(user.id)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_result(ip))

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/profile/interviewers", headers={"Authorization": "Bearer tok"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_create_interviewer_profile(self):
        user = _make_user(tier="pro")
        db = AsyncMock()
        empty_result = MagicMock()
        empty_result.scalars.return_value.all.return_value = []
        db.execute = AsyncMock(return_value=empty_result)

        def _add_side_effect(obj):
            from backend.db.models.interviewer_profile import InterviewerProfile as IP
            if isinstance(obj, IP):
                obj.id = uuid.uuid4()
                if obj.known_questions is None:
                    obj.known_questions = []
                obj.created_at = datetime.now(timezone.utc)

        db.add = MagicMock(side_effect=_add_side_effect)
        db.flush = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/profile/interviewers",
                json={"name": "Jane Smith", "company": "Acme", "interview_style": "behavioral"},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 201
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_free_tier_blocked_at_profile_limit(self):
        user = _make_user(tier="free")
        ip = _make_interviewer_profile(user.id)
        db = AsyncMock()
        full_result = MagicMock()
        full_result.scalars.return_value.all.return_value = [ip]  # already at limit=1
        db.execute = AsyncMock(return_value=full_result)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/profile/interviewers",
                json={"name": "Bob"},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 403
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_delete_nonexistent_profile_returns_404(self):
        user = _make_user()
        db = AsyncMock()
        db.get = AsyncMock(return_value=None)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.delete(
                f"/profile/interviewers/{uuid.uuid4()}",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 404
        app.dependency_overrides = {}


# ── Sessions ──────────────────────────────────────────────────────────────────

class TestSessions:
    @pytest.mark.asyncio
    async def test_create_session(self):
        user = _make_user(tier="pro")
        db = AsyncMock()

        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        db.execute = AsyncMock(return_value=count_result)

        def _add_side_effect(obj):
            from backend.db.models.session import Session as S
            if isinstance(obj, S):
                obj.id = uuid.uuid4()
                obj.created_at = datetime.now(timezone.utc)

        db.add = MagicMock(side_effect=_add_side_effect)
        db.flush = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/sessions",
                json={},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 201
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_list_sessions(self):
        user = _make_user()
        session = _make_session(user.id)
        db = AsyncMock()
        result = MagicMock()
        result.scalars.return_value.all.return_value = [session]
        db.execute = AsyncMock(return_value=result)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/sessions", headers={"Authorization": "Bearer tok"})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        user = _make_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                f"/sessions/{uuid.uuid4()}",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 404
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_delete_session(self):
        user = _make_user()
        session = _make_session(user.id)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_result(session))
        db.delete = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.delete(
                f"/sessions/{session.id}",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 204
        db.delete.assert_called_once_with(session)
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_free_tier_blocked_at_session_limit(self):
        user = _make_user(tier="free")
        db = AsyncMock()
        # Simulate count of 3 sessions (at the free limit)
        count_result = MagicMock()
        count_result.scalar_one.return_value = 3
        db.execute = AsyncMock(return_value=count_result)

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                "/sessions",
                json={},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 403
        app.dependency_overrides = {}


# ── Files ─────────────────────────────────────────────────────────────────────

class TestFiles:
    @pytest.mark.asyncio
    async def test_attach_file_returns_presigned_url(self):
        user = _make_user()
        session = _make_session(user.id)
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_result(session))

        def _add_side_effect(obj):
            from backend.db.models.attached_file import AttachedFile as AF
            if isinstance(obj, AF):
                obj.id = uuid.uuid4()
                obj.uploaded_at = datetime.now(timezone.utc)

        db.add = MagicMock(side_effect=_add_side_effect)
        db.flush = AsyncMock()

        with (
            patch("backend.routers.files.generate_presigned_upload_url") as mock_s3,
            patch("backend.routers.files.s3_object_url") as mock_url,
        ):
            mock_s3.return_value = {"url": "https://s3.example.com", "fields": {}, "key": "k"}
            mock_url.return_value = "https://s3.example.com/k"

            app.dependency_overrides = {
                get_current_user: lambda: user,
                get_db: _make_get_db(db),
            }
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as c:
                resp = await c.post(
                    f"/sessions/{session.id}/files",
                    json={"label": "Job Description", "filename": "jd.pdf", "content_type": "application/pdf"},
                    headers={"Authorization": "Bearer tok"},
                )
            assert resp.status_code == 201
            body = resp.json()
            assert "upload" in body
            assert body["upload"]["url"] == "https://s3.example.com"
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_attach_file_session_not_found(self):
        user = _make_user()
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_result(None))

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.post(
                f"/sessions/{uuid.uuid4()}/files",
                json={"label": "x", "filename": "f.pdf"},
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 404
        app.dependency_overrides = {}


# ── Reports ───────────────────────────────────────────────────────────────────

class TestReports:
    @pytest.mark.asyncio
    async def test_get_report_free_tier_blocked(self):
        user = _make_user(tier="free")
        db = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                f"/sessions/{uuid.uuid4()}/report",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 403
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_get_report_not_ready_returns_404(self):
        user = _make_user(tier="pro")
        session = _make_session(user.id)
        db = AsyncMock()

        # First execute: session found; second execute: no report
        db.execute = AsyncMock(
            side_effect=[_scalar_result(session), _scalar_result(None)]
        )

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                f"/sessions/{session.id}/report",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 404
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_get_report_returns_data(self):
        user = _make_user(tier="pro")
        session = _make_session(user.id)
        report = _make_report(session.id)
        db = AsyncMock()
        db.execute = AsyncMock(
            side_effect=[_scalar_result(session), _scalar_result(report)]
        )

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                f"/sessions/{session.id}/report",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == str(session.id)
        app.dependency_overrides = {}

    @pytest.mark.asyncio
    async def test_pdf_export_requires_teams_tier(self):
        user = _make_user(tier="pro")
        db = AsyncMock()

        app.dependency_overrides = {
            get_current_user: lambda: user,
            get_db: _make_get_db(db),
        }
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get(
                f"/sessions/{uuid.uuid4()}/report/pdf",
                headers={"Authorization": "Bearer tok"},
            )
        assert resp.status_code == 403
        app.dependency_overrides = {}


# ── Factory helpers ────────────────────────────────────────────────────────────

def _make_get_db(db):
    async def _get():
        yield db
    return _get


def _make_candidate_profile(user_id: uuid.UUID) -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = user_id
    p.resume_url = None
    p.parsed_resume = None
    p.target_role = "Engineer"
    p.target_salary_usd = None
    p.skills = ["Python"]
    p.weak_areas = []
    p.custom_notes = None
    p.updated_at = datetime.now(timezone.utc)
    return p


def _make_interviewer_profile(user_id: uuid.UUID) -> MagicMock:
    p = MagicMock()
    p.id = uuid.uuid4()
    p.user_id = user_id
    p.name = "Jane Smith"
    p.company = "Acme"
    p.role = "Engineering Manager"
    p.interview_style = "behavioral"
    p.known_questions = []
    p.notes = None
    p.created_at = datetime.now(timezone.utc)
    return p


def _make_session(user_id: uuid.UUID) -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = user_id
    s.candidate_profile_id = None
    s.interviewer_profile_id = None
    s.status = "active"
    s.started_at = datetime.now(timezone.utc)
    s.ended_at = None
    s.created_at = datetime.now(timezone.utc)
    s.attached_files = []
    s.turns = []
    return s


def _make_attached_file(session_id: uuid.UUID) -> MagicMock:
    f = MagicMock()
    f.id = uuid.uuid4()
    f.session_id = session_id
    f.label = "JD"
    f.file_url = "https://s3.example.com/k"
    f.file_type = "application/pdf"
    f.uploaded_at = datetime.now(timezone.utc)
    return f


def _make_report(session_id: uuid.UUID) -> MagicMock:
    r = MagicMock()
    r.id = uuid.uuid4()
    r.session_id = session_id
    r.overall_score = 7.5
    r.category_scores = {"technical": 8.0, "behavioral": 7.0, "communication": 7.5}
    r.strengths = ["Good communication"]
    r.weaknesses = ["Needs more examples"]
    r.interviewer_intent_summary = "Testing core backend skills."
    r.recommended_practice = ["Practice system design"]
    r.pdf_report_url = "https://bucket.s3.amazonaws.com/reports/test.pdf"
    r.generated_at = datetime.now(timezone.utc)
    return r


def _mock_db_with_profile(profile) -> AsyncMock:
    db = AsyncMock()
    result = MagicMock()
    result.scalar_one_or_none.return_value = profile
    db.execute = AsyncMock(return_value=result)
    db.flush = AsyncMock()
    db.add = MagicMock()
    return db
