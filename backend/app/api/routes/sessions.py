"""
Questionnaire sessions: start a pass, submit answers one at a time, review.

The route layer loads state and persists answers; every decision about what comes
next is delegated to services/questionnaire.py so branching stays testable
without a database.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.routes.catalog import load_questions, question_to_out
from app.db.session import get_db
from app.models import (
    Condition,
    Patient,
    PatientAnswer,
    PatientProfile,
    Question,
    QuestionnaireSession,
    TreatmentCategory,
    TreatmentPlan,
)
from app.models.enums import SessionStatus
from app.schemas.clinical import (
    AnswerOut,
    AnswerRequest,
    CategoryOut,
    ConditionOut,
    PatientOut,
    PatientProfileOut,
    ProgressOut,
    SessionStartRequest,
    SessionStateOut,
    SessionSummaryOut,
)
from app.services.questionnaire import (
    OptionSnapshot,
    QuestionnaireError,
    QuestionSnapshot,
    entry_question,
    first_unanswered,
    progress,
    reachable_path,
    resolve_next,
    validate_answer,
)

router = APIRouter(prefix="/api/sessions", tags=["questionnaire"])


def _to_snapshots(questions: Sequence[Question]) -> list[QuestionSnapshot]:
    """Convert ORM rows into the pure snapshots the traversal logic works on."""
    return [
        QuestionSnapshot(
            question_id=str(q.id),
            key=q.key,
            text=q.text,
            display_order=q.display_order,
            question_type=q.question_type,
            help_text=q.help_text,
            is_entry=q.is_entry,
            options=tuple(
                OptionSnapshot(
                    option_id=str(o.id),
                    label=o.label,
                    value=o.value,
                    display_order=o.display_order,
                    next_question_id=str(o.next_question_id) if o.next_question_id else None,
                    is_terminal=o.is_terminal,
                )
                for o in q.options
            ),
        )
        for q in questions
    ]


async def _answered_ids(db: AsyncSession, session_id: uuid.UUID) -> list[str]:
    rows = (
        await db.execute(
            select(PatientAnswer.question_id).where(PatientAnswer.session_id == session_id)
        )
    ).scalars().all()
    return [str(r) for r in rows]


async def _get_session(db: AsyncSession, session_id: uuid.UUID) -> QuestionnaireSession:
    session = await db.scalar(
        select(QuestionnaireSession).where(QuestionnaireSession.id == session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


async def _state(
    db: AsyncSession,
    session: QuestionnaireSession,
    *,
    question: Optional[Question],
    is_complete: bool,
) -> SessionStateOut:
    answered = await _answered_ids(db, session.id)
    questions = await load_questions(db, session.condition_id) if session.condition_id else []
    answered_count, total = progress(_to_snapshots(questions), len(answered))
    return SessionStateOut(
        session_id=session.id,
        patient_id=session.patient_id,
        condition_id=session.condition_id,
        category_id=session.category_id,
        status=session.status,
        is_complete=is_complete,
        question=question_to_out(question) if question is not None else None,
        progress=ProgressOut(answered=answered_count, total=total),
    )


@router.post("", response_model=SessionStateOut, status_code=status.HTTP_201_CREATED)
async def start_session(
    payload: SessionStartRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionStateOut:
    """Begin a questionnaire pass and return the first question."""
    patient = await db.scalar(select(Patient).where(Patient.id == payload.patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    condition = await db.scalar(select(Condition).where(Condition.id == payload.condition_id))
    if condition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found.")

    questions = await load_questions(db, condition.id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "No questions are configured for this condition yet. "
                "Please ask the department to complete the setup."
            ),
        )

    first = entry_question(_to_snapshots(questions))
    first_row = next((q for q in questions if str(q.id) == first.question_id), None) if first else None

    session = QuestionnaireSession(
        patient_id=patient.id,
        category_id=condition.category_id,
        condition_id=condition.id,
        status=SessionStatus.ACTIVE.value,
        current_question_id=first_row.id if first_row else None,
    )
    db.add(session)
    await db.flush()

    return await _state(db, session, question=first_row, is_complete=first_row is None)


@router.get("/{session_id}", response_model=SessionStateOut)
async def get_session_state(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionStateOut:
    """
    Current position in the flow.

    Used to resume after a refresh. If the stored current question has since been
    deactivated, the earliest unanswered question is served instead of erroring.
    """
    session = await _get_session(db, session_id)

    if session.status == SessionStatus.COMPLETED.value:
        return await _state(db, session, question=None, is_complete=True)

    questions = await load_questions(db, session.condition_id) if session.condition_id else []
    current = next((q for q in questions if q.id == session.current_question_id), None)

    if current is None:
        step = first_unanswered(_to_snapshots(questions), await _answered_ids(db, session.id))
        if step.question is None:
            return await _state(db, session, question=None, is_complete=True)
        current = next((q for q in questions if str(q.id) == step.question.question_id), None)
        session.current_question_id = current.id if current else None

    return await _state(db, session, question=current, is_complete=False)


@router.post("/{session_id}/answers", response_model=SessionStateOut)
async def submit_answer(
    session_id: uuid.UUID,
    payload: AnswerRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionStateOut:
    """
    Record one answer and return the next question, or completion.

    A completed questionnaire still accepts a correction to a question it already
    contains, because the review screen lets a patient fix a mis-tap before
    submitting. It does not accept a brand-new answer, which would mean extending
    a finished pass.
    """
    session = await _get_session(db, session_id)
    if not session.condition_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="This session has no condition set."
        )

    questions = await load_questions(db, session.condition_id)
    snapshots = _to_snapshots(questions)

    try:
        question_snapshot, option_snapshot = validate_answer(
            snapshots, str(payload.question_id), str(payload.option_id)
        )
    except QuestionnaireError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    existing = await db.scalar(
        select(PatientAnswer).where(
            PatientAnswer.session_id == session.id,
            PatientAnswer.question_id == payload.question_id,
        )
    )

    if session.status == SessionStatus.COMPLETED.value and existing is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This questionnaire is already complete. Existing answers can be "
                "corrected, but new questions cannot be added."
            ),
        )

    is_correction = existing is not None
    if existing is not None:
        # Update in place rather than appending, so the summary and the rule engine
        # always see exactly one answer per question.
        existing.selected_option_id = payload.option_id
        existing.answer_value = option_snapshot.value
        existing.answer_label = option_snapshot.label
        existing.answered_at = datetime.now(timezone.utc)
    else:
        db.add(
            PatientAnswer(
                session_id=session.id,
                patient_id=session.patient_id,
                question_id=payload.question_id,
                selected_option_id=payload.option_id,
                question_key=question_snapshot.key,
                answer_value=option_snapshot.value,
                answer_label=option_snapshot.label,
            )
        )
    await db.flush()

    if is_correction:
        return await _reroute_after_correction(db, session, questions, snapshots)

    step = resolve_next(
        snapshots,
        question_snapshot,
        option_snapshot,
        answered_question_ids=await _answered_ids(db, session.id),
    )

    if step.is_complete or step.question is None:
        session.status = SessionStatus.COMPLETED.value
        session.current_question_id = None
        session.completed_at = datetime.now(timezone.utc)
        await db.flush()
        return await _state(db, session, question=None, is_complete=True)

    next_row = next((q for q in questions if str(q.id) == step.question.question_id), None)
    session.current_question_id = next_row.id if next_row else None
    await db.flush()

    return await _state(db, session, question=next_row, is_complete=False)


async def _reroute_after_correction(
    db: AsyncSession,
    session: QuestionnaireSession,
    questions: Sequence[Question],
    snapshots: Sequence[QuestionSnapshot],
) -> SessionStateOut:
    """
    Replay the flow after an answer was changed.

    Changing a branching answer can move the patient onto a different route. Any
    answer from the abandoned branch is deleted, because leaving it in place would
    let a question the patient is no longer being asked go on driving the
    recommendation. It can also open up questions not yet answered, in which case
    the session reopens.
    """
    answers = (
        await db.execute(
            select(PatientAnswer).where(PatientAnswer.session_id == session.id)
        )
    ).scalars().all()
    answer_map = {str(a.question_id): str(a.selected_option_id) for a in answers}

    path = reachable_path(snapshots, answer_map)

    if path.orphaned_question_ids:
        orphans = {uuid.UUID(qid) for qid in path.orphaned_question_ids}
        await db.execute(
            delete(PatientAnswer).where(
                PatientAnswer.session_id == session.id,
                PatientAnswer.question_id.in_(orphans),
            )
        )
        await db.flush()

    # A previously generated plan is now based on superseded answers. Drop it so
    # the results screen has to re-evaluate rather than showing stale advice.
    # Reports are untouched: each is an immutable snapshot of what was issued.
    await db.execute(delete(TreatmentPlan).where(TreatmentPlan.session_id == session.id))

    if path.next_question is None:
        session.status = SessionStatus.COMPLETED.value
        session.current_question_id = None
        session.completed_at = session.completed_at or datetime.now(timezone.utc)
        await db.flush()
        return await _state(db, session, question=None, is_complete=True)

    next_row = next(
        (q for q in questions if str(q.id) == path.next_question.question_id), None
    )
    session.status = SessionStatus.IN_PROGRESS.value
    session.current_question_id = next_row.id if next_row else None
    session.completed_at = None
    await db.flush()

    return await _state(db, session, question=next_row, is_complete=False)


@router.get("/{session_id}/summary", response_model=SessionSummaryOut)
async def get_summary(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SessionSummaryOut:
    """Every answer given, for the review screen before submitting."""
    session = await _get_session(db, session_id)

    patient = await db.scalar(select(Patient).where(Patient.id == session.patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    profile = await db.scalar(
        select(PatientProfile)
        .where(PatientProfile.patient_id == patient.id)
        .order_by(PatientProfile.created_at.desc())
    )
    patient_out = PatientOut.model_validate(patient)
    if profile is not None:
        patient_out.profile = PatientProfileOut.model_validate(profile)

    category = (
        await db.scalar(select(TreatmentCategory).where(TreatmentCategory.id == session.category_id))
        if session.category_id
        else None
    )
    condition = (
        await db.scalar(select(Condition).where(Condition.id == session.condition_id))
        if session.condition_id
        else None
    )

    answers = (
        await db.execute(
            select(PatientAnswer)
            .where(PatientAnswer.session_id == session.id)
            .order_by(PatientAnswer.answered_at)
        )
    ).scalars().all()

    # Question wording is fetched for display; the stored key and label remain
    # the record of what was actually asked and answered.
    texts: dict[uuid.UUID, str] = {}
    if answers:
        rows = (
            await db.execute(
                select(Question.id, Question.text).where(
                    Question.id.in_([a.question_id for a in answers])
                )
            )
        ).all()
        texts = {row[0]: row[1] for row in rows}

    answer_out = []
    for answer in answers:
        item = AnswerOut.model_validate(answer)
        item.question_text = texts.get(answer.question_id, answer.question_key)
        answer_out.append(item)

    return SessionSummaryOut(
        session_id=session.id,
        patient=patient_out,
        category=CategoryOut.model_validate(category) if category else None,
        condition=ConditionOut.model_validate(condition) if condition else None,
        status=session.status,
        answers=answer_out,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )
