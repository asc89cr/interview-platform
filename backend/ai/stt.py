"""Deepgram Nova-2 streaming speech-to-text wrapper.

Accepts raw PCM audio frames from an asyncio.Queue and yields Turn objects
as speech is detected. Retries the Deepgram connection on transient failures.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Literal

from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveOptions,
    LiveTranscriptionEvents,
)

from backend.ai.types import Turn

logger = logging.getLogger(__name__)

_DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
_RECONNECT_DELAY: float = 2.0
_MAX_RETRIES: int = 3


async def transcribe_stream(
    audio_queue: asyncio.Queue,
    speaker: Literal["Interviewer", "Candidate"] = "Interviewer",
) -> AsyncIterator[Turn]:
    """Yield Turn(speaker, text) objects as Deepgram detects speech.

    Args:
        audio_queue: Queue of prefixed PCM frames (bytes). First byte is the
            speaker indicator (0x00=Interviewer, 0x01=Candidate) and is stripped
            before sending to Deepgram. Put ``None`` to signal end of stream.
        speaker: Fixed speaker label for every turn produced by this stream.
            Each speaker runs on its own Deepgram connection so labels are
            deterministic (no cross-contamination between mic and loopback).
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        result_queue: asyncio.Queue[Turn | None] = asyncio.Queue()
        feeder_task: asyncio.Task | None = None

        try:
            client = DeepgramClient(
                _DEEPGRAM_API_KEY,
                DeepgramClientOptions(options={"keepalive": "true"}),
            )
            connection = client.listen.asyncwebsocket.v("1")

            async def on_message(self, result, **_kwargs) -> None:
                if not result.is_final:
                    return
                alt = result.channel.alternatives[0]
                if not alt.transcript or not alt.transcript.strip():
                    return
                await result_queue.put(  # noqa: B023
                    Turn(speaker=speaker, text=alt.transcript.strip(), confidence=alt.confidence)
                )

            async def on_error(self, error, **_kwargs) -> None:
                logger.error("Deepgram error: %s", error)

            connection.on(LiveTranscriptionEvents.Transcript, on_message)
            connection.on(LiveTranscriptionEvents.Error, on_error)

            options = LiveOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
                interim_results=True,
                endpointing=300,
                channels=1,
                sample_rate=16_000,
                encoding="linear16",
            )
            await connection.start(options)
            logger.info(
                "Deepgram connection established for %s (attempt %d/%d)",
                speaker, attempt, _MAX_RETRIES,
            )

            async def _feed_audio(
                _conn: Any = connection,
                _audio: asyncio.Queue = audio_queue,
                _results: asyncio.Queue = result_queue,
            ) -> None:
                while True:
                    frame = await _audio.get()
                    if frame is None:  # end-of-stream sentinel
                        await _conn.finish()
                        await _results.put(None)
                        break
                    # First byte = speaker prefix (already routed); strip it.
                    await _conn.send(frame[1:])

            feeder_task = asyncio.create_task(_feed_audio())

            while True:
                turn = await result_queue.get()
                if turn is None:
                    break
                yield turn

            await feeder_task
            return  # clean exit — no retry needed

        except Exception as exc:
            if feeder_task and not feeder_task.done():
                feeder_task.cancel()
            logger.warning("STT attempt %d/%d failed: %s", attempt, _MAX_RETRIES, exc)
            if attempt == _MAX_RETRIES:
                raise
            await asyncio.sleep(_RECONNECT_DELAY * attempt)
