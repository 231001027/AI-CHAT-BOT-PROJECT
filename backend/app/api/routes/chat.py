"""Free-text chat → AI intent classification (session flow) + public assistant chat."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import cache_session_state
from app.db.session import get_db
from app.models import ChatSession
from app.models.enums import SessionStatus, SessionStep
from app.schemas import ChatMessageRequest, ChatMessageResponse
from app.services import ai_intent
from app.services import assistant_chat as public_assistant
from app.services import state_machine as sm

router = APIRouter(prefix="/api/chat", tags=["Chat"])
public_router = APIRouter(prefix="/api", tags=["Assistant Chat"])


class PublicChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


class PublicChatResponse(BaseModel):
    response: str
    followups: list[str]
    matched_keywords: list[str]
    source: str = "keyword"


@public_router.post("/chat", response_model=PublicChatResponse)
async def public_assistant_chat(body: PublicChatRequest) -> PublicChatResponse:
    """RAG-grounded AI assistant for /ai-assistant (Ollama + Qdrant corpus)."""
    result = await public_assistant.answer_message_async(body.message)
    return PublicChatResponse(**result)


@router.post("/message", response_model=ChatMessageResponse)
async def chat_message(body: ChatMessageRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, body.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.status != SessionStatus.ACTIVE.value:
        raise HTTPException(status_code=409, detail="Session is not active")

    current = sm.parse_step(session.current_step)
    # Free-text classification is allowed from concern_select (and symptoms for re-ask)
    sm.assert_step(
        current,
        {SessionStep.CONCERN_SELECT, SessionStep.SYMPTOMS, SessionStep.PROFILE},
        "chat_message",
    )

    result = ai_intent.classify_concern(body.message)

    history = list(session.chat_history or [])
    history.append({"role": "user", "content": body.message})
    history.append(
        {
            "role": "assistant",
            "content": result.reply,
            "concern_type": result.concern_type.value if result.concern_type else None,
            "confidence": result.confidence,
        }
    )
    session.chat_history = history

    ctx = dict(session.context or {})
    if result.concern_type:
        ctx["suggested_concern_type"] = result.concern_type.value
    session.context = ctx
    await db.flush()

    await cache_session_state(
        str(session.id),
        {
            "current_step": session.current_step,
            "status": session.status,
            "patient_id": str(session.patient_id) if session.patient_id else None,
            "context": session.context or {},
        },
    )

    suggested_band = None
    if ctx.get("suggested_age_band"):
        from app.models.enums import AgeBand

        suggested_band = AgeBand(ctx["suggested_age_band"])

    return ChatMessageResponse(
        session_id=session.id,
        concern_type=result.concern_type,
        confidence=result.confidence,
        reply=result.reply,
        current_step=current,
        suggested_age_band=suggested_band,
    )


@router.post("/phrase")
async def phrase_content(payload: dict, db: AsyncSession = Depends(get_db)):
    """Optional helper: warm-phrase static content via Claude (no routing)."""
    text = payload.get("text") or ""
    if not text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    result = ai_intent.phrase_static_content(text, context=payload.get("context"))
    return {"phrased": result.phrased}
