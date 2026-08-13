"""Relay raw PCM audio frames from the WebSocket queue into Deepgram STT.

Frames are prefixed with a 1-byte speaker indicator (0x00=Interviewer via system
loopback, 0x01=Candidate via microphone). We use a SINGLE Deepgram streaming
connection (Deepgram plans cap concurrent live connections, and one connection
is lowest-latency). Only the interviewer (loopback) audio is transcribed — that
is what drives auto-answer — so speaker labels are unambiguous and the candidate
mic never contaminates the interviewer transcript.

Produces Turn objects into ``turn_queue`` and terminates it with ``None``
once the audio stream ends or the Deepgram connection closes.
"""
from __future__ import annotations

import asyncio
import logging

from backend.ai.stt import transcribe_stream
from backend.ai.types import Turn

logger = logging.getLogger(__name__)


async def run_audio_router(
    audio_queue: asyncio.Queue[bytes | None],
    turn_queue: asyncio.Queue[Turn | None],
) -> None:
    """Drain ``audio_queue`` through Deepgram and forward Turn objects to ``turn_queue``.

    A ``None`` sentinel in ``audio_queue`` signals end-of-stream and causes
    the Deepgram connection to close cleanly.  A matching ``None`` is placed
    in ``turn_queue`` so that the answer router can stop.
    """
    try:
        async for turn in transcribe_stream(audio_queue):
            await turn_queue.put(turn)
    except Exception as exc:
        logger.error("Audio router failed: %s", exc)
    finally:
        await turn_queue.put(None)
