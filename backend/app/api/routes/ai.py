"""
AI Treatment Assistant endpoints.

The model only rephrases retrieved departmental text. Which tests were
recommended was already decided deterministically by the rule engine, and if
retrieval or the model is unavailable the admin-authored fallback is served.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentDoctor
from app.db.session import get_db
from app.models import AiConversation, Patient, PatientProfile, QuestionnaireSession
from app.schemas.clinical import (
    AiConversationOut,
    ExplainTestRequest,
    ExplanationOut,
    SourceChunkOut,
)
from app.services.ai.rag_pipeline import explain_test, rag_status

router = APIRouter(prefix="/api/ai", tags=["ai"])

# Excerpt length shown to the patient as a citation.
_EXCERPT_CHARS = 320


@router.post("/explain-test", response_model=ExplanationOut)
async def explain(
    payload: ExplainTestRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ExplanationOut:
    """Produce a grounded, patient-friendly explanation of one recommended test."""
    patient: Optional[Patient] = None
    profile: Optional[PatientProfile] = None

    patient_id = payload.patient_id
    if payload.session_id and patient_id is None:
        session = await db.scalar(
            select(QuestionnaireSession).where(QuestionnaireSession.id == payload.session_id)
        )
        if session is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        patient_id = session.patient_id

    if patient_id is not None:
        patient = await db.scalar(select(Patient).where(Patient.id == patient_id))
        if patient is not None:
            profile = await db.scalar(
                select(PatientProfile)
                .where(PatientProfile.patient_id == patient.id)
                .order_by(PatientProfile.created_at.desc())
            )

    result = await explain_test(
        db,
        test_name=payload.test_name.strip(),
        test_code=payload.test_code,
        flow_type=profile.flow_type if profile else None,
        child_subtype=profile.child_subtype if profile else None,
        patient_age=patient.age if patient else None,
        question=payload.question,
        patient_id=patient.id if patient else None,
        session_id=payload.session_id,
    )

    return ExplanationOut(
        test_name=result.test_name,
        explanation=result.explanation,
        source=result.source,
        model=result.model,
        sources=[
            SourceChunkOut(
                document_id=uuid.UUID(chunk.document_id) if chunk.document_id else None,
                title=chunk.title,
                chunk_index=chunk.chunk_index,
                score=round(chunk.score, 4),
                excerpt=chunk.text[:_EXCERPT_CHARS].strip(),
            )
            for chunk in result.chunks
        ],
    )


@router.get("/conversations/{session_id}", response_model=list[AiConversationOut])
async def get_conversations(
    session_id: uuid.UUID,
    _doctor: CurrentDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[AiConversationOut]:
    """
    Audit trail for a session.

    Staff-only: these rows contain the retrieved clinical context alongside the
    patient's question, and are treated as clinical records.
    """
    rows = (
        await db.execute(
            select(AiConversation)
            .where(AiConversation.session_id == session_id)
            .order_by(AiConversation.created_at)
        )
    ).scalars().all()
    return [AiConversationOut.model_validate(row) for row in rows]


@router.get("/status")
async def status_endpoint() -> dict[str, object]:
    """
    Whether retrieval and generation are currently available.

    Public so the patient UI can decide whether to offer AI explanations at all
    rather than showing a control that always falls back.
    """
    return await rag_status()
