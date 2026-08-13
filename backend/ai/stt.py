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
    """Yield Turn(speaker, text) objects as Deepgram detects the interviewer's speech.

    A single Deepgram connection is used. Only interviewer frames (prefix 0x00,
    from system loopback) are forwarded to Deepgram; candidate/mic frames
    (prefix 0x01) are dropped so they can't contaminate the interviewer
    transcript or trigger spurious answers. Every produced Turn is labeled
    "Interviewer".

    Args:
        audio_queue: Queue of prefixed PCM frames (bytes). First byte is the
            speaker indicator (0x00=Interviewer, 0x01=Candidate) and is stripped
            before sending to Deepgram. Put ``None`` to signal end of stream.
        speaker: Label applied to every produced turn (default "Interviewer").
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
                logger.info("STT final [%s]: %s", speaker, alt.transcript.strip())
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
                sent = 0
                dropped = 0
                while True:
                    frame = await _audio.get()
                    if frame is None:  # end-of-stream sentinel
                        await _conn.finish()
                        await _results.put(None)
                        break
                    if not frame:
                        continue
                    # First byte = speaker prefix. Only forward interviewer
                    # (loopback) audio; drop candidate/mic frames.
                    if frame[0] != 0x00:
                        dropped += 1
                        continue
                    await _conn.send(frame[1:])
                    sent += 1
                    if sent % 50 == 1:
                        logger.info(
                            "STT feeding interviewer audio: sent=%d dropped=%d", sent, dropped
                        )

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
