"""Real-time answer generation via OpenAI GPT-4o-mini.

Streams answer tokens as they arrive so the WebSocket layer can push
them to the client overlay with minimal latency.
Target TTFT: < 600 ms on US East region.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from backend.ai.types import AnswerContext

_MODEL = "gpt-4o-mini"
_MAX_TOKENS = 512
_TEMPERATURE = 0.7

_client: AsyncOpenAI | None = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


async def stream_answer(context: AnswerContext) -> AsyncIterator[str]:
    """Yield answer tokens from GPT-4o-mini for the given AnswerContext.

    The caller should iterate and forward each token over the WebSocket:

        async for token in stream_answer(ctx):
            await websocket.send_text(token)
    """
    messages = _build_messages(context)

    stream = await _get_client().chat.completions.create(
        model=_MODEL,
        messages=messages,  # type: ignore[arg-type]
        max_tokens=_MAX_TOKENS,
        temperature=_TEMPERATURE,
        stream=True,
    )

    async for chunk in stream:  # type: ignore[union-attr]
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def _build_messages(context: AnswerContext) -> list[dict]:
    """Build the OpenAI messages list from context."""
    messages: list[dict] = [{"role": "system", "content": context.system_prompt}]

    # Inject trimmed conversation history for continuity
    for turn in context.conversation_history:
        role = "user" if turn.speaker == "Interviewer" else "assistant"
        messages.append({"role": role, "content": turn.text})

    # The current interviewer question
    messages.append({"role": "user", "content": context.question_text})
    return messages
