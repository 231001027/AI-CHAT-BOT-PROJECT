"""Chat engine endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.chat_engine import find_response, match_keywords
from app.schemas import ChatRequest, ChatResponse

logger = logging.getLogger("hearconnect.chat")

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest):
    """
    Accept a user message and return a contextual hearing-care response.

    Matches keywords against a curated rule set. If nothing matches, returns
    a generic follow-up prompting the user to book an assessment.
    """
    logger.info("chat | message_len=%d", len(body.message))
    rule = find_response(body.message)
    return {
        "response": rule.response,
        "followups": rule.followups,
        "matched_keywords": match_keywords(body.message, rule),
    }
