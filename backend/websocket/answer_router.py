"""Process Interviewer turns and stream AI-generated answer tokens back over WebSocket.

For each Interviewer turn received from ``turn_queue``:
  1. Persist the Turn to the database.
  2. Build an AnswerContext from session context.
  3. Stream GPT-4o-mini tokens back to the client.
  4. Persist the generated answer.

Candidate turns (transcribed from the mic) are persisted but do not trigger
answer generation.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import WebSocket
from sqlalchemy.ext.asyncio import AsyncSession

from backend.ai.answer_agent import stream_answer
from backend.ai.context_builder import build_context
from backend.ai.types import (
    AnswerContext,
    AttachedFile as AIFile,
    CandidateProfile as AICandidateProfile,
    InterviewerProfile as AIInterviewerProfile,
    Turn as AITurn,
)
from backend.db.models.session import Session
from backend.db.models.turn import Turn

logger = logging.getLogger(__name__)


async def run_answer_router(
    turn_queue: asyncio.Queue[AITurn | None],
    websocket: WebSocket,
    db: AsyncSession,
    session: Session,
    ai_candidate: AICandidateProfile | None,
    ai_interviewer: AIInterviewerProfile | None,
    ai_files: list[AIFile],
    conversation_history: list[AITurn],
) -> None:
    """Consume turns from ``turn_queue``, stream answers, and persist everything.

    Args:
        turn_queue: Populated by the audio router; ``None`` signals end.
        websocket: Active WebSocket connection for streaming tokens to the client.
        db: Shared async DB session (commits handled by session_handler).
        session: The active Session ORM object.
        ai_candidate / ai_interviewer / ai_files: Pre-built AI context objects.
        conversation_history: Mutable list that grows as the session progresses.
    """
    while True:
        turn = await turn_queue.get()
        if turn is None:
            break

        # ── Persist the incoming turn ─────────────────────────────────────────
        db_turn = Turn(
            session_id=session.id,
            speaker=turn.speaker,
            text=turn.text,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(db_turn)
        await db.flush()
        conversation_history.append(turn)

        await websocket.send_text(
            json.dumps({
                "type": "turn_saved",
                "turn_id": str(db_turn.id),
                "speaker": turn.speaker,
            })
        )

        # ── Only Interviewer turns trigger answer generation ──────────────────
        if turn.speaker != "Interviewer":
            continue

        if ai_candidate is None or ai_interviewer is None:
            await websocket.send_text(
                json.dumps({"type": "error", "message": "Session not fully configured — missing profile"})
            )
            continue

        context: AnswerContext = build_context(
            turn=turn,
            candidate_profile=ai_candidate,
            interviewer_profile=ai_interviewer,
            attached_files=ai_files,
            conversation_history=conversation_history[:-1],  # exclude the just-added turn
        )

        # ── Stream answer tokens ──────────────────────────────────────────────
        full_answer = ""
        try:
            async for token in stream_answer(context):
                full_answer += token
                await websocket.send_text(json.dumps({"type": "token", "content": token}))
        except Exception as exc:
            logger.error("Answer streaming failed for session %s: %s", session.id, exc)
            await websocket.send_text(
                json.dumps({"type": "error", "message": "Answer generation failed"})
            )
            continue

        # ── Persist generated answer back onto the interviewer turn ───────────
        db_turn.generated_answer = full_answer
        await db.flush()

        # Also record as a Candidate answer turn so the transcript is complete
        candidate_turn = Turn(
            session_id=session.id,
            speaker="Candidate",
            text="",
            generated_answer=full_answer,
            timestamp=datetime.now(timezone.utc),
        )
        db.add(candidate_turn)
        await db.flush()

        conversation_history.append(
            AITurn(speaker="Candidate", text=full_answer, generated_answer=full_answer)
        )

        await websocket.send_text(
            json.dumps({"type": "answer_complete", "turn_id": str(candidate_turn.id)})
        )
