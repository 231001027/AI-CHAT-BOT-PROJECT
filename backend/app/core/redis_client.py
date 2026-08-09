"""Redis async client for session / chat state."""

from __future__ import annotations

import json
from typing import Any, Optional

import redis.asyncio as redis

from app.config import get_settings

_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        settings = get_settings()
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _session_key(session_id: str) -> str:
    return f"nipmed:session:{session_id}"


async def cache_session_state(session_id: str, state: dict[str, Any]) -> None:
    settings = get_settings()
    r = await get_redis()
    await r.set(
        _session_key(session_id),
        json.dumps(state),
        ex=settings.redis_session_ttl_seconds,
    )


async def get_cached_session_state(session_id: str) -> Optional[dict[str, Any]]:
    r = await get_redis()
    raw = await r.get(_session_key(session_id))
    if not raw:
        return None
    return json.loads(raw)


async def delete_cached_session_state(session_id: str) -> None:
    r = await get_redis()
    await r.delete(_session_key(session_id))
