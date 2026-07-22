"""Redis-backed session state for live WebSocket sessions.

Holds conversation history so that if the desktop client disconnects briefly
it can reconnect and resume without losing transcript context.  State expires
after RECONNECT_TTL seconds — after that the session cannot be recovered.

Reads connection settings from:
    REDIS_URL  (default: redis://localhost:6379)
"""
from __future__ import annotations

import json
import os
from typing import Any

import redis.asyncio as aioredis

RECONNECT_TTL = 60  # seconds to hold state after a client disconnect

_REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")


def _make_client() -> aioredis.Redis:
    return aioredis.from_url(_REDIS_URL, decode_responses=True)


def _key(session_id: str) -> str:
    return f"ws:session:{session_id}"


async def save_session_state(
    session_id: str,
    state: dict[str, Any],
    ttl: int = RECONNECT_TTL,
) -> None:
    """Serialize and store session state with a TTL (seconds)."""
    async with _make_client() as redis:
        await redis.setex(_key(session_id), ttl, json.dumps(state))


async def load_session_state(session_id: str) -> dict[str, Any] | None:
    """Return stored session state, or None if not found / expired."""
    async with _make_client() as redis:
        raw = await redis.get(_key(session_id))
    return json.loads(raw) if raw else None


async def delete_session_state(session_id: str) -> None:
    """Remove session state (called on successful reconnect)."""
    async with _make_client() as redis:
        await redis.delete(_key(session_id))
