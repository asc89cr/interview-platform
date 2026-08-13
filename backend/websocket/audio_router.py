"""Relay raw PCM audio frames from the WebSocket queue into Deepgram STT.

Frames are prefixed with a 1-byte speaker indicator (0x00=Interviewer via system
loopback, 0x01=Candidate via microphone). To keep speaker labels deterministic —
and to stop the two sources from disrupting each other's endpointing — each
speaker is demultiplexed onto its own Deepgram connection.

Produces Turn objects into ``turn_queue`` and terminates it with ``None``
once both audio streams end.
"""
from __future__ import annotations

import asyncio
import logging

from backend.ai.stt import transcribe_stream
from backend.ai.types import Turn

logger = logging.getLogger(__name__)

_INTERVIEWER_PREFIX = 0x00


async def _pump(
    src_queue: asyncio.Queue,
    turn_queue: asyncio.Queue[Turn | None],
    speaker: str,
) -> None:
    """Run one Deepgram stream for a single speaker and forward its turns."""
    try:
        async for turn in transcribe_stream(src_queue, speaker=speaker):  # type: ignore[arg-type]
            await turn_queue.put(turn)
    except Exception as exc:
        logger.error("STT stream for %s failed: %s", speaker, exc)


async def run_audio_router(
    audio_queue: asyncio.Queue[bytes | None],
    turn_queue: asyncio.Queue[Turn | None],
) -> None:
    """Demux ``audio_queue`` by speaker prefix into two Deepgram streams.

    A ``None`` sentinel in ``audio_queue`` signals end-of-stream: both sub-streams
    are closed and a single ``None`` is placed in ``turn_queue`` so the answer
    router can stop.
    """
    interviewer_q: asyncio.Queue[bytes | None] = asyncio.Queue()
    candidate_q: asyncio.Queue[bytes | None] = asyncio.Queue()

    interviewer_task = asyncio.create_task(
        _pump(interviewer_q, turn_queue, "Interviewer")
    )
    candidate_task = asyncio.create_task(
        _pump(candidate_q, turn_queue, "Candidate")
    )

    try:
        while True:
            frame = await audio_queue.get()
            if frame is None:  # end-of-stream
                await interviewer_q.put(None)
                await candidate_q.put(None)
                break
            if not frame:
                continue
            if frame[0] == _INTERVIEWER_PREFIX:
                await interviewer_q.put(frame)
            else:
                await candidate_q.put(frame)
    except Exception as exc:
        logger.error("Audio router failed: %s", exc)
        await interviewer_q.put(None)
        await candidate_q.put(None)
    finally:
        await asyncio.gather(interviewer_task, candidate_task, return_exceptions=True)
        await turn_queue.put(None)

