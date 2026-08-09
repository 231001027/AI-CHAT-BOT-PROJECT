"""Chat session and message persistence endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ChatMessage, ChatSession
from app.schemas import (
    ChatMessageBulkCreate,
    ChatMessageCreate,
    ChatMessageOut,
    ChatSessionCreate,
    ChatSessionOut,
)

logger = logging.getLogger("hearconnect.sessions")

router = APIRouter(prefix="/api", tags=["Chat Sessions"])


@router.post("/chat-sessions", response_model=ChatSessionOut, status_code=201)
def create_chat_session(body: ChatSessionCreate, db: Session = Depends(get_db)):
    """Create a guided Q&A chat session for a topic."""
    row = ChatSession(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("chat session created | id=%s | topic=%s", row.id, row.topic_id)
    return row


@router.get("/chat-sessions/{session_id}", response_model=ChatSessionOut)
def get_chat_session(session_id: str, db: Session = Depends(get_db)):
    row = db.get(ChatSession, session_id)
    if not row:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return row


@router.post("/chat-messages", response_model=ChatMessageOut, status_code=201)
def create_chat_message(body: ChatMessageCreate, db: Session = Depends(get_db)):
    """Append a single message to an existing chat session."""
    session = db.get(ChatSession, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    row = ChatMessage(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/chat-messages/bulk", response_model=list[ChatMessageOut], status_code=201)
def create_chat_messages_bulk(body: ChatMessageBulkCreate, db: Session = Depends(get_db)):
    """Bulk-save multiple messages (used to flush a Q&A session)."""
    session_ids = {m.session_id for m in body.messages}
    for sid in session_ids:
        if not db.get(ChatSession, sid):
            raise HTTPException(status_code=404, detail=f"Chat session not found: {sid}")

    rows = [ChatMessage(**m.model_dump()) for m in body.messages]
    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)
    return rows


@router.get("/chat-sessions/{session_id}/messages", response_model=list[ChatMessageOut])
def list_session_messages(session_id: str, db: Session = Depends(get_db)):
    session = db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
