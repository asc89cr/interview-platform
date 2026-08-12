"""WebSocket endpoint for live interview sessions.

Protocol
--------
Client → Server (binary):  Raw PCM16 audio frames (16 kHz mono)
Client → Server (text/JSON):
    {"type": "session_end"}  — end the session and trigger analysis
    {"type": "ping"}         — keepalive

Server → Client (text/JSON):
    {"type": "connected",       "session_id": "<uuid>"}
    {"type": "turn_saved",      "turn_id": "<uuid>", "speaker": "Interviewer|Candidate"}
    {"type": "token",           "content": "<text>"}  — streaming answer token
    {"type": "answer_complete", "turn_id": "<uuid>"}
    {"type": "session_ended"}
    {"type": "error",           "message": "<text>"}
    {"type": "pong"}

Lifecycle
---------
1. Client connects with JWT in ?token= query param.
2. JWT is validated; session is loaded from DB.
3. Any prior Redis state (from a reconnect window) is restored.
4. Audio router and answer router tasks are started.
5. Main loop receives binary audio frames or JSON control messages.
6. On ``session_end``: flush tasks, mark session completed, trigger analysis.
7. On unexpected disconnect: conversation history is saved to Redis for 60 s.
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.websockets import WebSocket, WebSocketDisconnect
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.ai.types import (
    AttachedFile as AIFile,
)
from backend.ai.types import (
    CandidateProfile as AICandidateProfile,
)
from backend.ai.types import (
    InterviewerProfile as AIInterviewerProfile,
)
from backend.ai.types import (
    Turn as AITurn,
)
from backend.auth.jwt import decode_access_token
from backend.db.base import AsyncSessionLocal
from backend.db.models.candidate_profile import CandidateProfile
from backend.db.models.interviewer_profile import InterviewerProfile
from backend.db.models.session import Session
from backend.services.session_state import (
    delete_session_state,
    load_session_state,
    save_session_state,
)
from backend.websocket.answer_router import run_answer_router
from backend.websocket.audio_router import run_audio_router

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])


# ── Helpers ────────────────────────────────────────────────────────────────────

def _turns_to_dict(turns: list[AITurn]) -> list[dict]:
    return [{"speaker": t.speaker, "text": t.text} for t in turns]


def _turns_from_dict(raw: list[dict]) -> list[AITurn]:
    return [AITurn(speaker=t["speaker"], text=t["text"]) for t in raw]


async def _load_ai_context(
    session: Session,
    db,
) -> tuple[AICandidateProfile | None, AIInterviewerProfile | None, list[AIFile]]:
    """Build lightweight AI context objects from DB-loaded ORM models."""
    ai_candidate: AICandidateProfile | None = None
    ai_interviewer: AIInterviewerProfile | None = None

    if session.candidate_profile_id:
        cp = await db.get(CandidateProfile, session.candidate_profile_id)
        if cp:
            ai_candidate = AICandidateProfile(
                id=str(cp.id),
                target_role=cp.target_role,
                skills=cp.skills,
                weak_areas=cp.weak_areas,
                custom_notes=cp.custom_notes,
                parsed_resume=cp.parsed_resume,
            )

    if session.interviewer_profile_id:
        ip = await db.get(InterviewerProfile, session.interviewer_profile_id)
        if ip:
            ai_interviewer = AIInterviewerProfile(
                id=str(ip.id),
                name=ip.name,
                company=ip.company,
                role=ip.role,
                interview_style=ip.interview_style,
                known_questions=ip.known_questions,
                notes=ip.notes,
            )

    # Load attached files (content extraction is handled by AI Integration Agent)
    result = await db.execute(
        select(Session)
        .options(selectinload(Session.attached_files))
        .where(Session.id == session.id)
    )
    full_session = result.scalar_one_or_none()
    ai_files: list[AIFile] = (
        [AIFile(filename=f.label, content="") for f in full_session.attached_files]
        if full_session
        else []
    )

    return ai_candidate, ai_interviewer, ai_files


async def _trigger_analysis(session_id: uuid.UUID) -> None:
    """Signal the Analysis Agent to process the completed session transcript.

    Currently logs the intent; in production this publishes to a task queue
    (Redis Streams, SQS, Celery, etc.) that the AI Integration Agent consumes.
    """
    logger.info("Post-session analysis triggered for session %s", session_id)


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/session/{session_id}")
async def websocket_session(
    websocket: WebSocket,
    session_id: uuid.UUID,
) -> None:
    # ── 1. Validate JWT from ?token= query param ─────────────────────────────
    query_token = websocket.query_params.get("token", "")
    try:
        payload = decode_access_token(query_token)
        user_id = uuid.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        await websocket.close(code=4001, reason="Invalid or missing token")
        return

    await websocket.accept()

    async with AsyncSessionLocal() as db:
        # ── 2. Load session, verify ownership ───────────────────────────────
        result = await db.execute(
            select(Session).where(Session.id == session_id, Session.user_id == user_id)
        )
        session = result.scalar_one_or_none()

        if session is None:
            await websocket.send_text(json.dumps({"type": "error", "message": "Session not found"}))
            await websocket.close(code=4004)
            return

        if session.status != "active":
            await websocket.send_text(
                json.dumps({"type": "error", "message": f"Session is {session.status}"})
            )
            await websocket.close(code=4003)
            return

        # ── 3. Build AI context + restore reconnect state ────────────────────
        ai_candidate, ai_interviewer, ai_files = await _load_ai_context(session, db)

        saved = await load_session_state(str(session_id))
        conversation_history: list[AITurn] = _turns_from_dict(saved["history"]) if saved else []
        if saved:
            await delete_session_state(str(session_id))

        await websocket.send_text(
            json.dumps({"type": "connected", "session_id": str(session_id)})
        )

        # ── 4. Start routing tasks ───────────────────────────────────────────
        audio_queue: asyncio.Queue[bytes | None] = asyncio.Queue()
        turn_queue: asyncio.Queue[AITurn | None] = asyncio.Queue()

        audio_task = asyncio.create_task(run_audio_router(audio_queue, turn_queue))
        answer_task = asyncio.create_task(
            run_answer_router(
                turn_queue=turn_queue,
                websocket=websocket,
                db=db,
                session=session,
                ai_candidate=ai_candidate,
                ai_interviewer=ai_interviewer,
                ai_files=ai_files,
                conversation_history=conversation_history,
            )
        )

        # ── 5. Main receive loop ─────────────────────────────────────────────
        try:
            while True:
                message = await websocket.receive()

                if message.get("bytes"):
                    await audio_queue.put(message["bytes"])

                elif message.get("text"):
                    try:
                        data = json.loads(message["text"])
                    except json.JSONDecodeError:
                        continue

                    msg_type = data.get("type")

                    if msg_type == "ping":
                        await websocket.send_text(json.dumps({"type": "pong"}))

                    elif msg_type == "force_answer":
                        # Try last Interviewer turn first; fall back to last turn of any speaker
                        last_interviewer = next(
                            (t for t in reversed(conversation_history) if t.speaker == "Interviewer"),
                            None,
                        ) or (conversation_history[-1] if conversation_history else None)
                        if last_interviewer:
                            await turn_queue.put(last_interviewer)
                        else:
                            await websocket.send_text(
                                json.dumps({"type": "error", "message": "No turns yet to answer"})
                            )

                    elif msg_type == "session_end":
                        await audio_queue.put(None)  # close Deepgram connection
                        await audio_task
                        await answer_task

                        session.status = "completed"
                        session.ended_at = datetime.now(timezone.utc)
                        await db.commit()

                        asyncio.create_task(_trigger_analysis(session_id))

                        await websocket.send_text(json.dumps({"type": "session_ended"}))
                        await websocket.close()
                        return

        except WebSocketDisconnect:
            logger.info("Client disconnected from session %s — preserving state", session_id)
        except Exception as exc:
            logger.error("WebSocket error for session %s: %s", session_id, exc)
        finally:
            # Cancel background tasks if still running
            if not audio_task.done():
                await audio_queue.put(None)
                audio_task.cancel()
            if not answer_task.done():
                answer_task.cancel()

            # ── 6. Persist conversation history to Redis (reconnect window) ───
            await save_session_state(
                str(session_id),
                {"history": _turns_to_dict(conversation_history)},
            )
            try:
                await db.commit()
            except Exception:
                await db.rollback()
