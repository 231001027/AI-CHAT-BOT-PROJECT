"""
Supervisor routing: decide which assistant should own an inbound message.

Two tiers, deliberately in this order:

1. Deterministic keyword scoring against each assistant's ``routing_keywords``.
   When it produces a clear winner we stop — it is free, instant and auditable.
2. Claude tool-calling, used only when keywords are ambiguous or absent.

Routing chooses a *destination*, never a clinical answer, so an LLM is safe here.
A wrong route costs one redirect; the destination assistant still applies its own
guardrails.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from anthropic import APIError, AsyncAnthropic

from app.agents.registry import list_agents
from app.config import get_settings
from app.models.enums import AgentType
from app.services.knowledge_base import stem, stem_all, tokenize

logger = logging.getLogger("nipmed.agents.router")

# A keyword decision needs this much of a lead over the runner-up to be trusted.
CONFIDENT_MARGIN = 1.0

# Where to send a message we genuinely cannot classify.
DEFAULT_AGENT = AgentType.ENQUIRY


@dataclass(frozen=True)
class RoutingDecision:
    agent_type: AgentType
    confidence: float
    method: str
    rationale: str = ""


def score_agents(message: str) -> dict[AgentType, float]:
    """
    Keyword overlap score per assistant.

    Multi-word keywords are matched as substrings (so "next week" counts). Single
    words are matched on their stem, so "stammers" and "stammering" both hit the
    "stammer" keyword without matching unrelated words that merely contain it.
    """
    lowered = (message or "").lower()
    stems = stem_all(tokenize(lowered))
    scores: dict[AgentType, float] = {}

    for spec in list_agents():
        score = 0.0
        for keyword in spec.routing_keywords:
            if " " in keyword:
                if keyword in lowered:
                    score += 1.5
            elif stem(keyword) in stems:
                score += 1.0
        scores[spec.agent_type] = score
    return scores


def route_by_keywords(message: str) -> RoutingDecision:
    """Deterministic first pass."""
    scores = score_agents(message)
    ranked = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0].value))
    best, best_score = ranked[0]
    runner_up_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if best_score <= 0:
        return RoutingDecision(
            agent_type=DEFAULT_AGENT,
            confidence=0.0,
            method="default",
            rationale="No routing keyword matched",
        )

    margin = best_score - runner_up_score
    # Confidence rises with both the raw score and how far ahead the winner is.
    confidence = min(1.0, 0.4 + 0.15 * best_score + 0.1 * margin)
    return RoutingDecision(
        agent_type=best,
        confidence=round(confidence, 3),
        method="keyword" if margin >= CONFIDENT_MARGIN else "keyword_weak",
        rationale=f"score={best_score}, margin={margin}",
    )


def _tool_schema() -> dict:
    return {
        "name": "select_assistant",
        "description": (
            "Choose which departmental assistant should handle this message. "
            "Choose a destination only — do not answer the question."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "enum": [a.value for a in AgentType],
                    "description": "The assistant best suited to handle the message",
                },
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "rationale": {"type": "string", "description": "One short sentence"},
            },
            "required": ["agent_type", "confidence"],
        },
    }


async def route_by_llm(message: str) -> RoutingDecision:
    """Second pass, used only when keyword routing is not confident."""
    settings = get_settings()
    catalogue = "\n".join(
        f"- {spec.id} ({spec.vertical.value}): {spec.description}" for spec in list_agents()
    )
    try:
        client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=300,
            tools=[_tool_schema()],
            tool_choice={"type": "tool", "name": "select_assistant"},
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Route this message to exactly one assistant of the NIEPMD "
                        "Department of Speech, Hearing and Communication. Do not "
                        "answer it.\n\n"
                        f"Assistants:\n{catalogue}\n\n"
                        f"Message:\n{message}"
                    ),
                }
            ],
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "select_assistant":
                data = block.input if isinstance(block.input, dict) else json.loads(block.input)
                return RoutingDecision(
                    agent_type=AgentType(data["agent_type"]),
                    confidence=float(data.get("confidence", 0.5)),
                    method="llm",
                    rationale=str(data.get("rationale", "")),
                )
        logger.warning("Router returned no tool_use block")
    except (APIError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("LLM routing failed (%s) — keeping keyword decision", exc)

    return route_by_keywords(message)


async def route_message(message: str) -> RoutingDecision:
    """
    Pick the assistant for a message.

    Keyword routing decides on its own when confident; otherwise Claude breaks the
    tie, and if Claude is unavailable the keyword result stands.
    """
    keyword_decision = route_by_keywords(message)
    if keyword_decision.method == "keyword":
        return keyword_decision

    settings = get_settings()
    if not settings.anthropic_enabled:
        return keyword_decision

    return await route_by_llm(message)
