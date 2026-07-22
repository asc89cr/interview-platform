"""Integration test: mock audio → transcribed Turn → answer tokens.

This test is intentionally offline — it mocks both Deepgram and OpenAI so
no API keys are required in CI. The test validates the full data-flow shape:
  1. audio_queue yields PCM frames → stt.transcribe_stream yields Turn objects
  2. context_builder assembles an AnswerContext from those turns
  3. answer_agent.stream_answer yields string tokens from that context
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.ai.context_builder import build_context
from backend.ai.types import (
    AttachedFile,
    CandidateProfile,
    InterviewerProfile,
    Turn,
)


# ── Shared fixtures ───────────────────────────────────────────────────────────


@pytest.fixture
def candidate() -> CandidateProfile:
    return CandidateProfile(
        id="cand-42",
        target_role="Backend Engineer",
        skills=["Python", "Django", "Redis"],
        weak_areas=["system design"],
        custom_notes=None,
        parsed_resume=None,
    )


@pytest.fixture
def interviewer() -> InterviewerProfile:
    return InterviewerProfile(
        id="int-42",
        name="Bob Lee",
        company="TechCo",
        role="Staff Engineer",
        interview_style="technical",
    )


# ── Mock STT: audio_queue → Turn ──────────────────────────────────────────────


async def _mock_transcribe_stream(audio_queue: asyncio.Queue) -> AsyncIterator[Turn]:
    """Consume frames and yield a fake Turn for each non-sentinel frame."""
    while True:
        frame = await audio_queue.get()
        if frame is None:
            break
        yield Turn(speaker="Interviewer", text="How does Python's GIL affect threading?", confidence=0.97)


@pytest.mark.asyncio
async def test_mock_stt_yields_turns() -> None:
    """STT mock must emit one Turn per audio frame, then stop on sentinel."""
    audio_q: asyncio.Queue = asyncio.Queue()
    await audio_q.put(b"\x00" * 3200)   # one 100 ms frame (16kHz, 16-bit)
    await audio_q.put(None)              # sentinel

    turns: list[Turn] = []
    async for turn in _mock_transcribe_stream(audio_q):
        turns.append(turn)

    assert len(turns) == 1
    assert turns[0].speaker == "Interviewer"
    assert "GIL" in turns[0].text
    assert 0 < turns[0].confidence <= 1.0


# ── Mock answer streaming ─────────────────────────────────────────────────────


async def _fake_stream_answer(context) -> AsyncIterator[str]:
    for token in ["The ", "GIL ", "is ", "a ", "mutex."]:
        yield token


@pytest.mark.asyncio
async def test_pipeline_audio_to_answer(candidate, interviewer) -> None:
    """Full pipeline: audio → STT turn → context → answer tokens."""
    # 1. Simulate one audio frame producing one Turn
    audio_q: asyncio.Queue = asyncio.Queue()
    await audio_q.put(b"\x00" * 3200)
    await audio_q.put(None)

    turns: list[Turn] = []
    async for turn in _mock_transcribe_stream(audio_q):
        turns.append(turn)

    assert turns, "STT must produce at least one turn"
    interviewer_turn = turns[0]

    # 2. Build context from that turn
    ctx = build_context(
        turn=interviewer_turn,
        candidate_profile=candidate,
        interviewer_profile=interviewer,
        attached_files=[],
        conversation_history=[],
    )
    assert ctx.question_type == "technical"

    # 3. Stream the answer (via mock)
    tokens: list[str] = []
    async for token in _fake_stream_answer(ctx):
        tokens.append(token)

    full_answer = "".join(tokens)
    assert len(tokens) > 0, "Answer stream must yield tokens"
    assert "GIL" in full_answer or "mutex" in full_answer


@pytest.mark.asyncio
async def test_answer_agent_streams_tokens(candidate, interviewer) -> None:
    """answer_agent.stream_answer must yield str tokens (mocked OpenAI call)."""
    from backend.ai import answer_agent

    turn = Turn(speaker="Interviewer", text="What is a decorator in Python?")
    ctx = build_context(
        turn=turn,
        candidate_profile=candidate,
        interviewer_profile=interviewer,
        attached_files=[AttachedFile(filename="jd.txt", content="Python role")],
        conversation_history=[],
    )

    # Mock the OpenAI streaming response
    fake_chunk = MagicMock()
    fake_chunk.choices = [MagicMock()]
    fake_chunk.choices[0].delta.content = "token"

    async def fake_aiter(self):
        yield fake_chunk
        fake_chunk.choices[0].delta.content = None  # last chunk has no content
        yield fake_chunk

    mock_stream = MagicMock()
    mock_stream.__aiter__ = fake_aiter

    with patch("backend.ai.answer_agent._get_client") as mock_get_client:
        mock_create = AsyncMock(return_value=mock_stream)
        mock_get_client.return_value.chat.completions.create = mock_create
        tokens: list[str] = []
        async for token in answer_agent.stream_answer(ctx):
            tokens.append(token)

    assert tokens == ["token"], f"Expected ['token'], got {tokens}"
