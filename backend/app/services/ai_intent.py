"""
Claude API helpers for intent parsing and warm phrasing ONLY.

HARD CONSTRAINT: Never use this module to decide medical tests or routing.
Those decisions belong exclusively to rules_engine.py + ConcernConfig.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from anthropic import Anthropic, APIError
from pydantic import BaseModel, Field

from app.config import get_settings
from app.models.enums import ConcernType

logger = logging.getLogger("nipmed.ai_intent")

CONCERN_LABELS = {
    ConcernType.HEARING_DIFFICULTY: "Hearing Difficulty",
    ConcernType.TINNITUS: "Tinnitus / ringing in ears",
    ConcernType.HYPERACUSIS: "Hyperacusis / sound sensitivity",
    ConcernType.DIZZINESS_BALANCE: "Dizziness / balance problems",
    ConcernType.EAR_PAIN_DISCHARGE: "Ear pain / discharge",
    ConcernType.CHILD_CONCERNS: "Child hearing concerns",
}


class IntentResult(BaseModel):
    concern_type: Optional[ConcernType] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    reply: str
    rationale: str = ""


class PhrasingResult(BaseModel):
    phrased: str


def _client() -> Anthropic:
    settings = get_settings()
    if not settings.anthropic_api_key or settings.anthropic_api_key.startswith("sk-ant-your"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not configured. Set it in backend/.env to enable AI intent."
        )
    return Anthropic(api_key=settings.anthropic_api_key)


def _tool_schema_classify() -> dict[str, Any]:
    return {
        "name": "classify_hearing_concern",
        "description": (
            "Classify the user's free-text description into exactly one hearing-care "
            "concern category. Do NOT recommend medical tests."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "concern_type": {
                    "type": "string",
                    "enum": [c.value for c in ConcernType],
                    "description": "Matched concern category",
                },
                "confidence": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Confidence 0–1",
                },
                "reply": {
                    "type": "string",
                    "description": "Warm one-line reply acknowledging the concern (no test advice)",
                },
                "rationale": {
                    "type": "string",
                    "description": "Brief internal reason for the classification",
                },
            },
            "required": ["concern_type", "confidence", "reply"],
        },
    }


def _tool_schema_phrase() -> dict[str, Any]:
    return {
        "name": "phrase_content",
        "description": "Rephrase static clinical content in warm, plain language. Do not add new medical advice or tests.",
        "input_schema": {
            "type": "object",
            "properties": {
                "phrased": {
                    "type": "string",
                    "description": "Conversational rephrasing of the source text",
                },
            },
            "required": ["phrased"],
        },
    }


def _heuristic_classify(text: str) -> IntentResult:
    """Offline fallback when Anthropic is unavailable — keyword only, no test routing."""
    lowered = text.lower()
    rules: list[tuple[ConcernType, list[str]]] = [
        (ConcernType.CHILD_CONCERNS, ["child", "baby", "infant", "toddler", "son", "daughter", "newborn"]),
        (ConcernType.TINNITUS, ["ringing", "buzzing", "hissing", "tinnitus"]),
        (ConcernType.HYPERACUSIS, ["sensitive", "hyperacusis", "too loud", "sound sensitivity"]),
        (ConcernType.DIZZINESS_BALANCE, ["dizzy", "vertigo", "balance", "spinning"]),
        (ConcernType.EAR_PAIN_DISCHARGE, ["pain", "discharge", "infection", "fluid", "pus"]),
        (ConcernType.HEARING_DIFFICULTY, ["hear", "muffled", "hearing loss", "repeat", "deaf"]),
    ]
    for concern, keys in rules:
        if any(k in lowered for k in keys):
            label = CONCERN_LABELS[concern]
            return IntentResult(
                concern_type=concern,
                confidence=0.55,
                reply=f"It sounds like this may relate to {label}. I can guide you through the next steps.",
                rationale="heuristic_keyword_match",
            )
    return IntentResult(
        concern_type=None,
        confidence=0.0,
        reply=(
            "Thank you for sharing that. Could you tell me a bit more, or pick a concern "
            "category such as hearing difficulty, tinnitus, dizziness, or ear pain?"
        ),
        rationale="no_match",
    )


def classify_concern(message: str) -> IntentResult:
    """
    Parse free-text into a ConcernType using Claude tool-calling.
    Falls back to keyword heuristics if the API key is missing or the call fails.
    """
    settings = get_settings()
    try:
        client = _client()
        categories = "\n".join(f"- {c.value}: {CONCERN_LABELS[c]}" for c in ConcernType)
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=400,
            tools=[_tool_schema_classify()],
            tool_choice={"type": "tool", "name": "classify_hearing_concern"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "You are a triage assistant for NIPMED Audiology. "
                        "Classify the user message into ONE concern category. "
                        "Do NOT recommend tests, diagnoses, or treatments.\n\n"
                        f"Categories:\n{categories}\n\n"
                        f"User message:\n{message}"
                    ),
                }
            ],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "classify_hearing_concern":
                data = block.input if isinstance(block.input, dict) else json.loads(block.input)
                return IntentResult(
                    concern_type=ConcernType(data["concern_type"]),
                    confidence=float(data.get("confidence", 0.0)),
                    reply=str(data.get("reply", "")),
                    rationale=str(data.get("rationale", "")),
                )
        logger.warning("Claude returned no tool_use block; falling back to heuristic")
    except (RuntimeError, APIError, ValueError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("classify_concern fallback: %s", exc)

    return _heuristic_classify(message)


def phrase_static_content(source_text: str, context: Optional[str] = None) -> PhrasingResult:
    """
    Warm rephrasing of static content (e.g. a test explanation).
    Must not invent new medical recommendations.
    """
    settings = get_settings()
    try:
        client = _client()
        ctx = f"\nContext: {context}" if context else ""
        response = client.messages.create(
            model=settings.anthropic_model,
            max_tokens=300,
            tools=[_tool_schema_phrase()],
            tool_choice={"type": "tool", "name": "phrase_content"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Rephrase the following clinical text in warm, plain language for a patient. "
                        "Do not add new tests, diagnoses, or medical advice. Keep the meaning identical."
                        f"{ctx}\n\nText:\n{source_text}"
                    ),
                }
            ],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "phrase_content":
                data = block.input if isinstance(block.input, dict) else json.loads(block.input)
                return PhrasingResult(phrased=str(data["phrased"]))
    except (RuntimeError, APIError, ValueError, KeyError, json.JSONDecodeError) as exc:
        logger.warning("phrase_static_content fallback: %s", exc)

    return PhrasingResult(phrased=source_text)
