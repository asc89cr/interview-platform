"""Deepgram Nova-2 streaming speech-to-text wrapper.

Accepts raw PCM audio frames from an asyncio.Queue and yields Turn objects
as speech is detected. Retries the Deepgram connection on transient failures.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Any, Literal, cast

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


# Protocol: first byte of each frame is the speaker prefix sent by the desktop client.
# 0x00 = loopback / system audio → Interviewer
# 0x01 = microphone → Candidate
_SPEAKER_PREFIX: dict[int, str] = {0x00: "Interviewer", 0x01: "Candidate"}


async def transcribe_stream(audio_queue: asyncio.Queue) -> AsyncIterator[Turn]:
    """Yield Turn(speaker, text) objects as Deepgram detects speech.

    Args:
        audio_queue: Queue of prefixed PCM frames (bytes). First byte is the
            speaker indicator (0x00=Interviewer, 0x01=Candidate). Put ``None``
            to signal end of stream.
    """
    for attempt in range(1, _MAX_RETRIES + 1):
        result_queue: asyncio.Queue[Turn | None] = asyncio.Queue()
        feeder_task: asyncio.Task | None = None
        # Tracks the speaker of the most recently sent audio frame
        current_speaker: list[str] = ["Interviewer"]

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
                # Use the source-based speaker instead of diarization
                speaker = cast(Literal["Interviewer", "Candidate"], current_speaker[0])
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
                endpointing=700,
                channels=1,
                sample_rate=16_000,
                encoding="linear16",
            )
            await connection.start(options)
            logger.info("Deepgram connection established (attempt %d/%d)", attempt, _MAX_RETRIES)

            async def _feed_audio(
                _conn: Any = connection,
                _audio: asyncio.Queue = audio_queue,
                _results: asyncio.Queue = result_queue,
                _speaker: list[str] = current_speaker,
            ) -> None:
                while True:
                    frame = await _audio.get()
                    if frame is None:  # end-of-stream sentinel
                        await _conn.finish()
                        await _results.put(None)
                        break
                    # First byte = speaker prefix; remainder = raw PCM
                    _speaker[0] = _SPEAKER_PREFIX.get(frame[0], "Candidate")
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
