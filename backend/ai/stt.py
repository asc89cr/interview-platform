"""Deepgram Nova-2 streaming speech-to-text wrapper.

Accepts raw PCM audio frames from an asyncio.Queue and yields Turn objects
as speech is detected. Retries the Deepgram connection on transient failures.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import AsyncIterator
from typing import Literal, cast

from deepgram import DeepgramClient, DeepgramClientOptions, LiveOptions, LiveTranscriptionEvents

from backend.ai.types import Turn

logger = logging.getLogger(__name__)

_DEEPGRAM_API_KEY: str = os.getenv("DEEPGRAM_API_KEY", "")
_RECONNECT_DELAY: float = 2.0
_MAX_RETRIES: int = 3

# Speaker 0 is treated as the Interviewer (first detected speaker).
# The desktop client should use diarization channel 0 for system audio
# (interviewer's voice) and channel 1 for microphone (candidate).
_SPEAKER_MAP: dict[int, str] = {0: "Interviewer", 1: "Candidate"}


async def transcribe_stream(audio_queue: asyncio.Queue) -> AsyncIterator[Turn]:
    """Yield Turn(speaker, text) objects as Deepgram detects speech.

    Args:
        audio_queue: Queue of raw PCM frames (bytes). Put ``None`` to signal
            end of stream and close the Deepgram connection.
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

            async def on_message(self, result, **_kwargs) -> None:  # noqa: ANN001
                alt = result.channel.alternatives[0]
                if not alt.transcript:
                    return
                words = alt.words or []
                speaker_id: int = words[0].speaker if words else 0
                speaker = cast(Literal["Interviewer", "Candidate"], _SPEAKER_MAP.get(speaker_id, "Candidate"))
                await result_queue.put(
                    Turn(speaker=speaker, text=alt.transcript, confidence=alt.confidence)
                )

            async def on_error(self, error, **_kwargs) -> None:  # noqa: ANN001
                logger.error("Deepgram error: %s", error)

            connection.on(LiveTranscriptionEvents.Transcript, on_message)
            connection.on(LiveTranscriptionEvents.Error, on_error)

            options = LiveOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                diarize=True,
                channels=1,
                sample_rate=16_000,
                encoding="linear16",
            )
            await connection.start(options)
            logger.info("Deepgram connection established (attempt %d/%d)", attempt, _MAX_RETRIES)

            async def _feed_audio() -> None:
                while True:
                    frame = await audio_queue.get()
                    if frame is None:  # end-of-stream sentinel
                        await connection.finish()
                        await result_queue.put(None)
                        break
                    await connection.send(frame)

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
