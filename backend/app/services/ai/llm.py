"""
Shared LLM text generation for RAG explanations and simple phrasing.

Supports local Ollama, Anthropic Claude, and Google Gemini. Provider selection
is driven by ``Settings.llm_provider`` / ``active_llm_provider``. Tool-calling
agent loops still use Anthropic directly when that key is present.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings

logger = logging.getLogger("nipmed.llm")


async def generate_text(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: Optional[int] = None,
) -> Optional[str]:
    """
    Generate a plain-text completion.

    Returns None when no provider is configured or the call fails, so callers can
    fall back to static / extract text without raising into the request path.
    """
    settings = get_settings()
    provider = settings.active_llm_provider
    if provider is None:
        return None

    limit = max_tokens or settings.agent_max_tokens
    if provider == "ollama":
        return await _ollama(system_prompt, user_prompt, limit)
    if provider == "anthropic":
        return await _anthropic(system_prompt, user_prompt, limit)
    if provider == "gemini":
        return await _gemini(system_prompt, user_prompt, limit)
    return None


async def _ollama(system_prompt: str, user_prompt: str, max_tokens: int) -> Optional[str]:
    """
    Call a local Ollama instance via ``/api/chat``.

    Uses the OpenAI-compatible chat shape Ollama exposes locally — no cloud key.
    """
    settings = get_settings()
    base = settings.ollama_base_url.rstrip("/")
    url = f"{base}/api/chat"
    payload = {
        "model": settings.ollama_model,
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.3,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=settings.ollama_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("Ollama call failed (%s)", exc)
        return None

    message = data.get("message") if isinstance(data, dict) else None
    text = ""
    if isinstance(message, dict):
        text = str(message.get("content") or "").strip()
    if not text and isinstance(data, dict):
        # Older /api/generate-style responses (defensive).
        text = str(data.get("response") or "").strip()
    if not text:
        logger.warning("Ollama response missing text: %s", data)
        return None
    return text


async def _anthropic(system_prompt: str, user_prompt: str, max_tokens: int) -> Optional[str]:
    settings = get_settings()
    try:
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        logger.warning("Anthropic call failed (%s)", exc)
        return None

    parts = [block.text for block in response.content if getattr(block, "type", "") == "text"]
    text = "\n".join(p.strip() for p in parts if p and p.strip()).strip()
    return text or None


async def _gemini(system_prompt: str, user_prompt: str, max_tokens: int) -> Optional[str]:
    """
    Call the Gemini generateContent REST API.

    Kept as HTTP (no extra SDK) so the Gemini key in backend/.env is enough.
    """
    settings = get_settings()
    model = settings.gemini_model
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent"
    )
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": 0.3,
        },
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                url,
                params={"key": settings.gemini_api_key},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("Gemini call failed (%s)", exc)
        return None

    try:
        parts = data["candidates"][0]["content"]["parts"]
        text = "\n".join(
            str(p.get("text", "")).strip() for p in parts if p.get("text")
        ).strip()
    except (KeyError, IndexError, TypeError):
        logger.warning("Gemini response missing text candidates: %s", data)
        return None
    return text or None
