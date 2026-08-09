"""Symptom answer capture."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import ChatSession, Concern, SymptomResponse
from app.models.enums import SessionStatus, SessionStep
from app.schemas import SymptomAnswerRequest, SymptomAnswerResponse
from app.services import state_machine as sm

router = APIRouter(prefix="/api/symptoms", tags=["Symptoms"])


@router.post("/answer", response_model=SymptomAnswerResponse)
async def answer_symptom(body: SymptomAnswerRequest, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.ACTIVE.value:
        raise HTTPException(status_code=409, detail="Session is not active")

    current = sm.parse_step(session.current_step)
    sm.assert_step(current, {SessionStep.SYMPTOMS}, "answer_symptom")

    concern = await db.get(Concern, body.concern_id)
    if not concern:
        raise HTTPException(status_code=404, detail="Concern not found")
    if session.patient_id and concern.patient_id != session.patient_id:
        raise HTTPException(status_code=403, detail="Concern does not belong to this session's patient")

    # Upsert by concern_id + question_key
    existing = await db.execute(
        select(SymptomResponse).where(
            SymptomResponse.concern_id == body.concern_id,
            SymptomResponse.question_key == body.question_key,
        )
    )
    row = existing.scalar_one_or_none()
    if row:
        row.answer = body.answer
    else:
        row = SymptomResponse(
            concern_id=body.concern_id,
            question_key=body.question_key,
            answer=body.answer,
        )
        db.add(row)

    await db.flush()

    count_result = await db.execute(
        select(func.count()).select_from(SymptomResponse).where(
            SymptomResponse.concern_id == body.concern_id
        )
    )
    answers_so_far = int(count_result.scalar_one())

    return SymptomAnswerResponse(
        id=row.id,
        concern_id=body.concern_id,
        question_key=body.question_key,
        answer=body.answer,
        answers_so_far=answers_so_far,
        current_step=SessionStep.SYMPTOMS,
    )
