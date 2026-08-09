"""Assistant suite: discovery, routing, conversation and escalation."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base import AgentContext
from app.agents.registry import get_agent, list_agents, tools_for
from app.agents.router import route_message
from app.agents.runtime import run_agent
from app.agents.tools import escalate_to_staff
from app.db.session import get_db
from app.models import AgentConversation, AgentMessage
from app.models.enums import (
    AGENT_VERTICALS,
    AgentType,
    ConversationStatus,
    MessageRole,
    Vertical,
)
from app.schemas.agents import (
    AgentChatRequest,
    AgentChatResponse,
    AgentMessageOut,
    AgentSummary,
    ConversationOut,
    EscalationRequest,
    EscalationResponse,
    RouteRequest,
    RouteResponse,
    ToolCallOut,
)

router = APIRouter(prefix="/api/agents", tags=["Assistants"])

# How many prior turns are replayed to the model. Enough for a booking dialogue
# without letting the prompt grow unbounded.
HISTORY_TURNS = 12


@router.get("", response_model=list[AgentSummary])
async def get_agents():
    """Catalogue of the five departmental assistants."""
    return [
        AgentSummary(
            id=spec.id,
            name=spec.name,
            vertical=spec.vertical,
            tagline=spec.tagline,
            description=spec.description,
            capabilities=[t.name for t in tools_for(spec)],
            sample_prompts=list(spec.sample_prompts),
        )
        for spec in list_agents()
    ]


@router.post("/route", response_model=RouteResponse)
async def route(payload: RouteRequest):
    """Ask the supervisor which assistant should handle a message."""
    decision = await route_message(payload.message)
    spec = get_agent(decision.agent_type.value)
    if spec is None:  # pragma: no cover — routing only yields known agents
        raise HTTPException(status_code=500, detail="Router returned an unknown assistant")
    return RouteResponse(
        agent_id=spec.id,
        agent_name=spec.name,
        vertical=spec.vertical,
        confidence=decision.confidence,
        method=decision.method,
        rationale=decision.rationale,
    )


@router.post("/chat", response_model=AgentChatResponse)
async def auto_chat(payload: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """Route the message to the right assistant, then answer with it."""
    decision = await route_message(payload.message)
    return await _chat_with(
        decision.agent_type.value,
        payload,
        db,
        routed=True,
        routing_confidence=decision.confidence,
    )


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def agent_chat(agent_id: str, payload: AgentChatRequest, db: AsyncSession = Depends(get_db)):
    """Talk to one named assistant directly, skipping the supervisor."""
    return await _chat_with(agent_id, payload, db)


@router.get("/conversations/{conversation_id}", response_model=ConversationOut)
async def get_conversation(conversation_id: UUID, db: AsyncSession = Depends(get_db)):
    """Full transcript including tool calls — the audit trail for a conversation."""
    conversation = await db.get(AgentConversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    rows = (
        (
            await db.execute(
                select(AgentMessage)
                .where(AgentMessage.conversation_id == conversation_id)
                .order_by(AgentMessage.created_at, AgentMessage.id)
            )
        )
        .scalars()
        .all()
    )
    return ConversationOut(
        id=conversation.id,
        agent_id=conversation.agent_type,
        vertical=Vertical(conversation.vertical),
        status=conversation.status,
        context=conversation.context or {},
        messages=[
            AgentMessageOut(
                role=m.role,
                content=m.content,
                tool_calls=m.tool_calls,
                sources=m.sources,
                created_at=m.created_at,
            )
            for m in rows
        ],
        created_at=conversation.created_at,
    )


@router.post("/escalate", response_model=EscalationResponse, status_code=201)
async def escalate(payload: EscalationRequest, db: AsyncSession = Depends(get_db)):
    """Explicit human hand-off, e.g. from a 'talk to a person' button."""
    agent_type = AgentType.ENQUIRY
    if payload.agent_id:
        spec = get_agent(payload.agent_id)
        if spec is None:
            raise HTTPException(status_code=404, detail=f"Unknown assistant: {payload.agent_id}")
        agent_type = spec.agent_type

    result = await escalate_to_staff(
        db,
        reason=payload.reason,
        priority=payload.priority.value,
        agent_type=agent_type.value,
        vertical=AGENT_VERTICALS[agent_type].value,
        contact_name=payload.contact_name,
        contact_phone=payload.contact_phone,
        conversation_id=str(payload.conversation_id) if payload.conversation_id else None,
    )

    if payload.conversation_id:
        conversation = await db.get(AgentConversation, payload.conversation_id)
        if conversation is not None:
            conversation.status = ConversationStatus.ESCALATED.value

    await db.commit()
    return EscalationResponse(
        reference_code=result["reference_code"],
        priority=payload.priority,
        status="open",
        message=result["message"],
    )


# ---------------------------------------------------------------------------
# Shared chat handling
# ---------------------------------------------------------------------------


async def _chat_with(
    agent_id: str,
    payload: AgentChatRequest,
    db: AsyncSession,
    *,
    routed: bool = False,
    routing_confidence: float | None = None,
) -> AgentChatResponse:
    spec = get_agent(agent_id)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown assistant: {agent_id}")

    conversation = await _resolve_conversation(db, spec, payload)
    history = await _load_history(db, conversation.id)

    ctx = AgentContext(
        db=db,
        conversation_id=str(conversation.id),
        patient_id=str(conversation.patient_id) if conversation.patient_id else None,
        session_id=str(conversation.session_id) if conversation.session_id else None,
        history=history,
        memory=dict(conversation.context or {}),
    )

    db.add(
        AgentMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=payload.message,
        )
    )
    await db.flush()

    result = await run_agent(spec, ctx, payload.message)

    db.add(
        AgentMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=result.reply,
            tool_calls=[c.as_dict() for c in result.tool_calls] or None,
            sources=result.sources or None,
        )
    )
    if result.escalated:
        conversation.status = ConversationStatus.ESCALATED.value
    if result.memory:
        conversation.context = result.memory
    await db.commit()

    return AgentChatResponse(
        conversation_id=conversation.id,
        agent_id=spec.id,
        agent_name=spec.name,
        vertical=spec.vertical,
        reply=result.reply,
        tool_calls=[ToolCallOut(**c.as_dict()) for c in result.tool_calls],
        sources=result.sources,
        escalated=result.escalated,
        escalation_reference=result.escalation_reference,
        escalation_priority=result.escalation_priority,
        used_fallback=result.used_fallback,
        routed=routed,
        routing_confidence=routing_confidence,
    )


async def _resolve_conversation(
    db: AsyncSession, spec, payload: AgentChatRequest
) -> AgentConversation:
    """Reuse the caller's conversation when given, otherwise open a new one."""
    if payload.conversation_id:
        conversation = await db.get(AgentConversation, payload.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        # Switching assistants mid-conversation is expected when the supervisor
        # re-routes; record the change so the transcript stays truthful.
        if conversation.agent_type != spec.id:
            conversation.agent_type = spec.id
            conversation.vertical = spec.vertical.value
        return conversation

    conversation = AgentConversation(
        agent_type=spec.id,
        vertical=spec.vertical.value,
        session_id=payload.session_id,
        patient_id=payload.patient_id,
        status=ConversationStatus.ACTIVE.value,
        context={},
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def _load_history(db: AsyncSession, conversation_id: UUID) -> list[dict]:
    """
    Replay recent turns as plain text messages.

    Tool blocks are deliberately not replayed — Anthropic requires tool_use and
    tool_result blocks to be adjacent and complete, and reconstructing that from
    storage is fragile. Prose turns give the model enough continuity.
    """
    rows = (
        (
            await db.execute(
                select(AgentMessage)
                .where(
                    AgentMessage.conversation_id == conversation_id,
                    AgentMessage.role.in_([MessageRole.USER.value, MessageRole.ASSISTANT.value]),
                )
                .order_by(AgentMessage.created_at.desc(), AgentMessage.id.desc())
                .limit(HISTORY_TURNS)
            )
        )
        .scalars()
        .all()
    )
    ordered = list(reversed(rows))
    history: list[dict] = []
    for row in ordered:
        if not row.content.strip():
            continue
        history.append({"role": row.role, "content": row.content})

    # The Anthropic API rejects a leading assistant turn.
    while history and history[0]["role"] != MessageRole.USER.value:
        history.pop(0)
    return history
