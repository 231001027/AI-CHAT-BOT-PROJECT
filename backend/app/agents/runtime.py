"""
The agentic runtime.

One loop serves all five assistants:

1. Deterministic safety pre-screen. Red flags bypass the model completely.
2. Claude is called with the assistant's system prompt and its permitted tools.
3. While the model asks for tools, we execute them against the database and feed
   the results back, up to ``AGENT_MAX_TOOL_ITERATIONS`` round-trips.
4. The final text is returned along with a full audit trail of tool calls.

If no Anthropic key is configured the runtime degrades to a deterministic
fallback: it runs the assistant's primary tool and formats the result with fixed
templates. Every assistant therefore remains usable offline, which is also what
makes the suite testable without network access.
"""

from __future__ import annotations

import inspect
import json
import logging
from typing import Any, Optional

from anthropic import APIError, AsyncAnthropic

from app.agents.base import AgentContext, AgentReply, AgentSpec, ToolDef, ToolInvocation
from app.agents.registry import TOOLS, tools_for
from app.agents.tools import DEPARTMENT_CONTACT, escalate_to_staff
from app.config import get_settings
from app.services.knowledge_base import stem_all, tokenize
from app.services.safety import screen_message

logger = logging.getLogger("nipmed.agents.runtime")

# Context the runtime injects into handlers that declare these parameters, so the
# model can never spoof a conversation or patient id.
INJECTED_PARAMS = frozenset({"conversation_id", "patient_id", "agent_type", "vertical"})

GENERIC_FAILURE = (
    "I ran into a problem looking that up. Please try again, or call the "
    f"department on {DEPARTMENT_CONTACT['phone']} during working hours."
)


async def run_agent(spec: AgentSpec, ctx: AgentContext, message: str) -> AgentReply:
    """Handle one user turn for one assistant."""
    verdict = screen_message(message)
    if verdict.blocked:
        return await _handle_blocked(spec, ctx, message, verdict)

    settings = get_settings()
    if not settings.anthropic_enabled:
        logger.info("No Anthropic key configured — using deterministic fallback for %s", spec.id)
        return await _fallback_reply(spec, ctx, message)

    try:
        return await _run_llm_loop(spec, ctx, message)
    except (APIError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        logger.warning("Agent %s LLM loop failed (%s) — falling back", spec.id, exc)
        return await _fallback_reply(spec, ctx, message)


# ---------------------------------------------------------------------------
# LLM tool-use loop
# ---------------------------------------------------------------------------


async def _run_llm_loop(spec: AgentSpec, ctx: AgentContext, message: str) -> AgentReply:
    settings = get_settings()
    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    permitted = {t.name: t for t in tools_for(spec)}

    messages: list[dict[str, Any]] = [*ctx.history, {"role": "user", "content": message}]
    invocations: list[ToolInvocation] = []
    sources: list[str] = []
    escalation_reference: Optional[str] = None
    reply_text = ""

    for iteration in range(settings.agent_max_tool_iterations):
        response = await client.messages.create(
            model=settings.anthropic_model,
            max_tokens=settings.agent_max_tokens,
            system=spec.system_prompt(),
            tools=[t.as_anthropic_tool() for t in permitted.values()],
            messages=messages,
        )

        text_blocks = [b.text for b in response.content if b.type == "text"]
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if not tool_uses:
            reply_text = "\n\n".join(t.strip() for t in text_blocks if t.strip())
            break

        # Echo the assistant turn back verbatim; the API requires the tool_use
        # blocks to be present before their results.
        messages.append({"role": "assistant", "content": response.content})

        results: list[dict[str, Any]] = []
        for block in tool_uses:
            tool = permitted.get(block.name)
            args = block.input if isinstance(block.input, dict) else {}
            if tool is None:
                # The model asked for a tool outside this assistant's scope.
                logger.warning("Agent %s requested unpermitted tool %s", spec.id, block.name)
                output: dict[str, Any] = {
                    "error": "tool_not_available",
                    "message": f"{block.name} is not available to this assistant.",
                }
            else:
                output = await _execute_tool(tool, ctx, spec, args)

            invocations.append(ToolInvocation(tool=block.name, input=args, output=output))
            sources.extend(_extract_sources(output))
            if output.get("escalated") and output.get("reference_code"):
                escalation_reference = str(output["reference_code"])

            results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output, default=str),
                }
            )

        messages.append({"role": "user", "content": results})

        if iteration == settings.agent_max_tool_iterations - 1:
            # Out of budget: keep whatever prose we have rather than looping on.
            reply_text = "\n\n".join(t.strip() for t in text_blocks if t.strip())
            logger.warning("Agent %s hit the tool iteration cap", spec.id)

    if not reply_text:
        reply_text = _summarise_invocations(invocations) or GENERIC_FAILURE

    return AgentReply(
        agent_type=spec.agent_type,
        reply=reply_text,
        tool_calls=invocations,
        sources=_dedupe(sources),
        escalated=escalation_reference is not None,
        escalation_reference=escalation_reference,
        memory=ctx.memory,
    )


async def _execute_tool(
    tool: ToolDef, ctx: AgentContext, spec: AgentSpec, args: dict[str, Any]
) -> dict[str, Any]:
    """
    Call a handler with only the parameters it declares.

    Unknown keys from the model are dropped rather than causing a TypeError, and
    trusted context (conversation id, agent identity) is injected here so it
    cannot be supplied by the model.
    """
    signature = inspect.signature(tool.handler)
    accepted = set(signature.parameters)

    call_args: dict[str, Any] = {}
    for key, value in args.items():
        if key in accepted and key not in INJECTED_PARAMS:
            call_args[key] = value

    if "conversation_id" in accepted and ctx.conversation_id:
        call_args["conversation_id"] = ctx.conversation_id
    if "patient_id" in accepted and ctx.patient_id:
        call_args["patient_id"] = ctx.patient_id
    if "agent_type" in accepted:
        call_args["agent_type"] = spec.agent_type.value
    if "vertical" in accepted:
        call_args["vertical"] = spec.vertical.value

    try:
        return await tool.handler(ctx.db, **call_args)
    except Exception as exc:  # noqa: BLE001 — a tool fault must not kill the turn
        logger.exception("Tool %s failed", tool.name)
        return {"error": "tool_failed", "message": str(exc)}


# ---------------------------------------------------------------------------
# Safety blocking
# ---------------------------------------------------------------------------


async def _handle_blocked(
    spec: AgentSpec, ctx: AgentContext, message: str, verdict: Any
) -> AgentReply:
    """Return the fixed safety response, raising a ticket when a red flag fired."""
    invocations: list[ToolInvocation] = []
    reference: Optional[str] = None

    if verdict.escalate:
        reason = "; ".join(f.reason for f in verdict.flags) or "Safety red flag detected"
        args = {
            "reason": reason,
            "priority": verdict.priority.value if verdict.priority else "urgent",
            "triggers": verdict.trigger_codes,
        }
        output = await escalate_to_staff(
            ctx.db,
            reason=reason,
            priority=args["priority"],
            agent_type=spec.agent_type.value,
            vertical=spec.vertical.value,
            conversation_id=ctx.conversation_id,
            triggers=verdict.trigger_codes,
        )
        invocations.append(
            ToolInvocation(tool="escalate_to_staff", input=args, output=output)
        )
        reference = str(output.get("reference_code")) if output.get("reference_code") else None

    reply = verdict.message
    if reference:
        reply = f"{reply}\n\nReference: {reference}"

    return AgentReply(
        agent_type=spec.agent_type,
        reply=reply,
        tool_calls=invocations,
        escalated=verdict.escalate,
        escalation_reference=reference,
        escalation_priority=verdict.priority,
        memory=ctx.memory,
    )


# ---------------------------------------------------------------------------
# Deterministic fallback (no LLM available)
# ---------------------------------------------------------------------------


async def _fallback_reply(spec: AgentSpec, ctx: AgentContext, message: str) -> AgentReply:
    """
    Answer using the assistant's primary tool and fixed templates.

    Argument inference is intentionally crude — it only reads the age band and
    therapy domain out of the message. The point is a useful, honest answer
    without a model, not clever parsing.
    """
    invocations: list[ToolInvocation] = []
    sources: list[str] = []

    tool_name = spec.fallback_tool
    tool = TOOLS.get(tool_name) if tool_name else None
    if tool is None:
        return AgentReply(
            agent_type=spec.agent_type,
            reply=_fallback_intro(spec),
            used_fallback=True,
            memory=ctx.memory,
        )

    args = _infer_fallback_args(tool_name, message)
    output = await _execute_tool(tool, ctx, spec, args)
    invocations.append(ToolInvocation(tool=tool_name, input=args, output=output))
    sources.extend(_extract_sources(output))

    body = _format_tool_output(tool_name, output)
    if not body:
        body = (
            "I could not find departmental information for that. Please call "
            f"{DEPARTMENT_CONTACT['phone']} during working hours "
            f"({DEPARTMENT_CONTACT['working_hours']}) and our staff will help."
        )

    return AgentReply(
        agent_type=spec.agent_type,
        reply=f"{_fallback_intro(spec)}\n\n{body}",
        tool_calls=invocations,
        sources=_dedupe(sources),
        used_fallback=True,
        memory=ctx.memory,
    )


def _fallback_intro(spec: AgentSpec) -> str:
    return f"[{spec.name}]"


def _infer_fallback_args(tool_name: str, message: str) -> dict[str, Any]:
    """Best-effort arguments for the fallback tool call."""
    tokens = stem_all(tokenize(message))

    if tool_name in {"search_knowledge_base", "get_counselling_resources"}:
        args: dict[str, Any] = {"query": message}
        band = _guess_age_band(message, tokens)
        if band and tool_name == "get_counselling_resources":
            args["age_band"] = band
        return args

    if tool_name == "get_screening_protocol":
        band = _guess_age_band(message, tokens)
        return {"age_band": band} if band else {}

    if tool_name == "get_therapy_guideline":
        domain = _guess_therapy_domain(tokens)
        args = {"domain": domain} if domain else {}
        band = _guess_age_band(message, tokens)
        if band:
            args["age_band"] = band
        return args

    return {}


def _guess_age_band(message: str, tokens: set[str]) -> Optional[str]:
    """
    Infer an age band from wording, then from any explicit age.

    ``tokens`` may be raw or stemmed; it is re-stemmed here so callers do not have
    to care which they pass.
    """
    stems = stem_all(tokens)
    if stems & stem_all({"newborn", "birth", "nicu", "neonate"}):
        return "newborn"
    if stems & stem_all({"infant", "toddler", "baby", "babies"}):
        return "infant_toddler"
    if stems & stem_all({"preschool", "nursery", "kindergarten"}):
        return "preschool"
    if stems & stem_all({"school", "classroom", "class"}):
        return "school_age"

    years = _first_age_in_years(message)
    if years is None:
        return None
    if years < 0.5:
        return "newborn"
    if years < 2.5:
        return "infant_toddler"
    if years < 5:
        return "preschool"
    return "school_age"


def _first_age_in_years(message: str) -> Optional[float]:
    """Read the first age expression, e.g. '3 years', '18 months', '6-month-old'."""
    import re

    lowered = message.lower()
    month_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*month", lowered)
    if month_match:
        return float(month_match.group(1)) / 12
    year_match = re.search(r"(\d+(?:\.\d+)?)\s*[- ]?\s*(?:year|yr|y\.?o\.?)", lowered)
    if year_match:
        return float(year_match.group(1))
    return None


def _guess_therapy_domain(tokens: set[str]) -> Optional[str]:
    """
    Map wording to an SLP domain, most specific first.

    Order matters: feeding and voice are checked before the broader language and
    articulation buckets so "choking while feeding" does not land on articulation
    because it mentions a sound.
    """
    stems = stem_all(tokens)
    buckets: tuple[tuple[str, set[str]], ...] = (
        ("fluency", {"stammer", "stammering", "stutter", "stuttering", "fluency", "blocks"}),
        ("feeding_swallowing", {"swallow", "swallowing", "feeding", "choking", "chewing", "aspirate"}),
        ("voice", {"voice", "hoarse", "hoarseness", "nasal", "raspy"}),
        ("auditory_verbal", {"implant", "cochlear", "aid", "aids", "listening"}),
        ("articulation", {"pronounce", "pronunciation", "articulation", "sound", "sounds", "lisp", "unclear"}),
        ("language_delay", {"words", "sentence", "sentences", "language", "delay", "talking", "nonverbal", "vocabulary"}),
    )
    for domain, keywords in buckets:
        if stems & stem_all(keywords):
            return domain
    return None


def _format_tool_output(tool_name: str, output: dict[str, Any]) -> str:
    """Fixed templates so fallback replies never paraphrase clinical content."""
    if output.get("error"):
        return str(output.get("message") or GENERIC_FAILURE)

    if tool_name == "search_knowledge_base":
        if not output.get("found"):
            return ""
        return "\n\n".join(
            f"{r['topic']}\n{r['answer']}" for r in output.get("results", [])
        )

    if tool_name == "find_available_slots":
        if not output.get("found"):
            return str(output.get("message", ""))
        lines = [f"{i}. {s['human_readable']}" for i, s in enumerate(output.get("slots", []), 1)]
        return (
            "These slots are currently open:\n"
            + "\n".join(lines)
            + "\n\nReply with the number you want, along with the patient's full name "
            "and a phone number, and I will confirm the booking."
        )

    if tool_name == "list_screening_protocols":
        if not output.get("found"):
            return str(output.get("message", ""))
        blocks = [
            f"{p['name']} ({p['age_band'].replace('_', ' ')})\n{p['summary']}\nTiming: {p['timeline']}"
            for p in output.get("protocols", [])
        ]
        return "Our hearing screening pathways:\n\n" + "\n\n".join(blocks)

    if tool_name == "get_screening_protocol":
        if not output.get("found"):
            return str(output.get("message", ""))
        parts = [f"{output['name']}\n{output['summary']}"]
        tests = output.get("tests") or []
        if tests:
            parts.append(
                "Tests used:\n" + "\n".join(f"- {t['name']} — {t['description']}" for t in tests)
            )
        criteria = output.get("referral_criteria") or []
        if criteria:
            parts.append("Referral criteria:\n" + "\n".join(f"- {c}" for c in criteria))
        parts.append(f"Timing: {output['timeline']}")
        if output.get("preparation"):
            parts.append(f"Preparation: {output['preparation']}")
        return "\n\n".join(parts)

    if tool_name == "list_therapy_domains":
        if not output.get("found"):
            return str(output.get("message", ""))
        names = ", ".join(d["domain"].replace("_", " ") for d in output.get("domains", []))
        return (
            f"Our speech-language therapy guidance covers: {names}.\n\n"
            "Tell me which area your concern falls under and the age of the person, "
            "and I will share the department's guidance for it."
        )

    if tool_name == "get_therapy_guideline":
        if not output.get("found"):
            return str(output.get("message", ""))
        blocks: list[str] = []
        for g in output.get("guidelines", []):
            section = [f"{g['title']}\n{g['summary']}"]
            if g.get("milestones"):
                section.append(
                    "Typical milestones:\n" + "\n".join(f"- {m}" for m in g["milestones"])
                )
            if g.get("home_activities"):
                section.append(
                    "Things to try at home:\n" + "\n".join(f"- {a}" for a in g["home_activities"])
                )
            if g.get("red_flags"):
                section.append(
                    "See a therapist sooner if:\n" + "\n".join(f"- {f}" for f in g["red_flags"])
                )
            if g.get("typical_frequency"):
                section.append(f"Typical therapy frequency: {g['typical_frequency']}")
            blocks.append("\n\n".join(section))
        return "\n\n".join(blocks)

    if tool_name == "get_counselling_resources":
        if not output.get("found"):
            return str(output.get("message", ""))
        blocks = []
        for r in output.get("resources", []):
            section = [f"{r['topic']}\n{r['summary']}"]
            if r.get("talking_points"):
                section.append("\n".join(f"- {p}" for p in r["talking_points"]))
            if r.get("next_steps"):
                section.append("Next steps:\n" + "\n".join(f"- {s}" for s in r["next_steps"]))
            blocks.append("\n\n".join(section))
        return "\n\n".join(blocks)

    if tool_name == "list_services":
        if not output.get("found"):
            return str(output.get("message", ""))
        lines = [
            f"- {s['name']} ({s['duration_minutes']} min) — {s['description']}"
            for s in output.get("services", [])
        ]
        return "Services we offer:\n" + "\n".join(lines)

    return ""


def _summarise_invocations(invocations: list[ToolInvocation]) -> str:
    """Last-resort prose when the model returned tool calls but no text."""
    for inv in reversed(invocations):
        formatted = _format_tool_output(inv.tool, inv.output)
        if formatted:
            return formatted
    return ""


def _extract_sources(output: dict[str, Any]) -> list[str]:
    """Collect identifiers of the records that backed an answer, for audit."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("slug", "code", "reference_code", "age_band"):
                value = node.get(key)
                if isinstance(value, str) and value:
                    found.append(value)
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(output)
    return found


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for v in values:
        if v not in seen:
            seen.add(v)
            ordered.append(v)
    return ordered
