"""WebSocket integration tests (Agent 03).

Tests the /ws/session/{session_id} endpoint with mocked STT and LLM so no
live Deepgram or OpenAI connections are needed.

Run with:
    pytest backend/tests/test_websocket.py -v
"""
import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://localhost:5432/test_db")

import asyncio
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from backend.auth import jwt as jwt_utils
from backend.main import app

# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_session(user_id: uuid.UUID, status: str = "active") -> MagicMock:
    s = MagicMock()
    s.id = uuid.uuid4()
    s.user_id = user_id
    s.candidate_profile_id = None
    s.interviewer_profile_id = None
    s.status = status
    s.started_at = datetime.now(timezone.utc)
    s.ended_at = None
    s.created_at = datetime.now(timezone.utc)
    s.attached_files = []
    s.turns = []
    return s


def _valid_token(user_id: uuid.UUID) -> str:
    return jwt_utils.create_access_token(str(user_id))


# ── Tests ──────────────────────────────────────────────────────────────────────

class TestWebSocketSession:
    def test_invalid_token_rejected(self):
        """A WebSocket connection with an invalid token should be closed."""
        client = TestClient(app)
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/session/{uuid.uuid4()}?token=bad.token"):
                pass  # should not reach here

    def test_missing_token_rejected(self):
        """A WebSocket connection with no token should be rejected."""
        client = TestClient(app)
        with pytest.raises(Exception):
            with client.websocket_connect(f"/ws/session/{uuid.uuid4()}"):
                pass

    def test_session_not_found_closes_connection(self):
        """Valid JWT but non-existent session should close with error."""
        user_id = uuid.uuid4()
        token = _valid_token(user_id)
        session_id = uuid.uuid4()

        mock_session_obj = AsyncMock()
        mock_session_obj.__aenter__ = AsyncMock(return_value=mock_session_obj)
        mock_session_obj.__aexit__ = AsyncMock(return_value=False)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = None
        mock_session_obj.execute = AsyncMock(return_value=scalar_result)
        mock_session_obj.commit = AsyncMock()
        mock_session_obj.rollback = AsyncMock()

        with (
            patch("backend.websocket.session_handler.AsyncSessionLocal", return_value=mock_session_obj),
            patch("backend.websocket.session_handler.save_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.load_session_state", new_callable=AsyncMock, return_value=None),
            patch("backend.websocket.session_handler.delete_session_state", new_callable=AsyncMock),
        ):
            client = TestClient(app)
            with client.websocket_connect(f"/ws/session/{session_id}?token={token}") as ws:
                msg = ws.receive_text()
                data = json.loads(msg)
                assert data["type"] == "error"
                assert "not found" in data["message"].lower()

    def test_completed_session_rejected(self):
        """A session that is already 'completed' should not accept a WS connection."""
        user_id = uuid.uuid4()
        token = _valid_token(user_id)
        session = _make_session(user_id, status="completed")

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = session
        mock_db.execute = AsyncMock(return_value=scalar_result)
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()

        with (
            patch("backend.websocket.session_handler.AsyncSessionLocal", return_value=mock_db),
            patch("backend.websocket.session_handler.save_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.load_session_state", new_callable=AsyncMock, return_value=None),
            patch("backend.websocket.session_handler.delete_session_state", new_callable=AsyncMock),
        ):
            client = TestClient(app)
            with client.websocket_connect(f"/ws/session/{session.id}?token={token}") as ws:
                msg = ws.receive_text()
                data = json.loads(msg)
                assert data["type"] == "error"
                assert "completed" in data["message"]

    def test_connect_sends_connected_message(self):
        """A valid connection should receive a 'connected' confirmation."""
        user_id = uuid.uuid4()
        token = _valid_token(user_id)
        session = _make_session(user_id, status="active")

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.get = AsyncMock(return_value=None)

        # First execute: load session; second: load attached files
        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = session
        mock_db.execute = AsyncMock(return_value=scalar_result)

        # Patch audio_router to never produce turns (blocks forever → simulates live silence)
        async def _silent_audio(audio_q, turn_q):
            await asyncio.sleep(100)

        async def _silent_answer(**_kwargs):
            await asyncio.sleep(100)

        with (
            patch("backend.websocket.session_handler.AsyncSessionLocal", return_value=mock_db),
            patch("backend.websocket.session_handler.load_session_state", new_callable=AsyncMock, return_value=None),
            patch("backend.websocket.session_handler.delete_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.save_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.run_audio_router", _silent_audio),
            patch("backend.websocket.session_handler.run_answer_router", _silent_answer),
        ):
            client = TestClient(app)
            with client.websocket_connect(f"/ws/session/{session.id}?token={token}") as ws:
                msg = ws.receive_text()
                data = json.loads(msg)
                assert data["type"] == "connected"
                assert data["session_id"] == str(session.id)

    def test_ping_pong(self):
        """The server should respond to a ping with a pong."""
        user_id = uuid.uuid4()
        token = _valid_token(user_id)
        session = _make_session(user_id, status="active")

        mock_db = AsyncMock()
        mock_db.__aenter__ = AsyncMock(return_value=mock_db)
        mock_db.__aexit__ = AsyncMock(return_value=False)
        mock_db.commit = AsyncMock()
        mock_db.rollback = AsyncMock()
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()
        mock_db.get = AsyncMock(return_value=None)

        scalar_result = MagicMock()
        scalar_result.scalar_one_or_none.return_value = session
        mock_db.execute = AsyncMock(return_value=scalar_result)

        async def _noop_audio(audio_q, turn_q):
            await asyncio.sleep(100)

        async def _noop_answer(**_kwargs):
            await asyncio.sleep(100)

        with (
            patch("backend.websocket.session_handler.AsyncSessionLocal", return_value=mock_db),
            patch("backend.websocket.session_handler.load_session_state", new_callable=AsyncMock, return_value=None),
            patch("backend.websocket.session_handler.delete_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.save_session_state", new_callable=AsyncMock),
            patch("backend.websocket.session_handler.run_audio_router", _noop_audio),
            patch("backend.websocket.session_handler.run_answer_router", _noop_answer),
        ):
            client = TestClient(app)
            with client.websocket_connect(f"/ws/session/{session.id}?token={token}") as ws:
                ws.receive_text()  # "connected"
                ws.send_text(json.dumps({"type": "ping"}))
                pong = json.loads(ws.receive_text())
                assert pong["type"] == "pong"
