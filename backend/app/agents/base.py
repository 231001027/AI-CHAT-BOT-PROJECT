"""Core types shared by every departmental assistant."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AgentType, EscalationPriority, Vertical

# Guardrails prepended to every assistant's system prompt. Kept in one place so a
# policy change applies to the whole suite at once.
SHARED_GUARDRAILS = """
You are an assistant for the Department of Speech, Hearing and Communication at
NIEPMD (National Institute for Empowerment of Persons with Multiple
Disabilities), Chennai.

Non-negotiable rules:
1. Never diagnose a condition, interpret test results, or advise on medication,
   dosage or surgery. Redirect those to a qualified clinician.
2. State clinical facts ONLY from the output of your tools. If a tool returns
   nothing relevant, say you do not have that information and offer to connect
   the person to departmental staff. Never fill gaps from your own knowledge.
3. Do not invent appointment times, fees, phone numbers, staff names or
   protocols. Every such detail must come from a tool result.
4. If the person describes a medical emergency, tell them to seek immediate
   in-person care and use the escalate_to_staff tool.
5. Keep replies short and plain — 2 to 4 short paragraphs or a brief list.
   Write for an anxious patient or parent, not a clinician. Avoid jargon; when a
   clinical term is unavoidable, gloss it in a few words.
6. You may answer in the language the person writes in.
7. Never claim to be a doctor, audiologist or therapist. You are an assistant
   that provides information and arranges appointments.
""".strip()


@dataclass(frozen=True)
class ToolDef:
    """
    One capability an assistant can invoke.

    ``handler`` receives the live DB session plus the model-supplied arguments
    and returns a JSON-serialisable dict that is fed back to the model.
    """

    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Awaitable[dict[str, Any]]]

    def as_anthropic_tool(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


@dataclass(frozen=True)
class AgentSpec:
    """Static definition of one assistant."""

    agent_type: AgentType
    name: str
    vertical: Vertical
    tagline: str
    description: str
    instructions: str
    tool_names: tuple[str, ...]
    # Tool run when no LLM is available, so the assistant still works offline.
    fallback_tool: Optional[str] = None
    sample_prompts: tuple[str, ...] = ()
    # Keywords the supervisor uses to route free text without an LLM.
    routing_keywords: tuple[str, ...] = ()

    @property
    def id(self) -> str:
        return self.agent_type.value

    def system_prompt(self) -> str:
        return f"{SHARED_GUARDRAILS}\n\n--- Your specific role ---\n{self.instructions.strip()}"


@dataclass
class AgentContext:
    """Per-request state handed to the runtime."""

    db: AsyncSession
    conversation_id: Optional[str] = None
    patient_id: Optional[str] = None
    session_id: Optional[str] = None
    # Prior turns as Anthropic message dicts, oldest first.
    history: list[dict[str, Any]] = field(default_factory=list)
    # Assistant working memory persisted on AgentConversation.context.
    memory: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolInvocation:
    """Audit record of a single tool call."""

    tool: str
    input: dict[str, Any]
    output: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {"tool": self.tool, "input": self.input, "output": self.output}


@dataclass
class AgentReply:
    """What an assistant hands back to the API layer."""

    agent_type: AgentType
    reply: str
    tool_calls: list[ToolInvocation] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    escalated: bool = False
    escalation_reference: Optional[str] = None
    escalation_priority: Optional[EscalationPriority] = None
    # True when the reply came from deterministic fallback rather than the model.
    used_fallback: bool = False
    memory: dict[str, Any] = field(default_factory=dict)
