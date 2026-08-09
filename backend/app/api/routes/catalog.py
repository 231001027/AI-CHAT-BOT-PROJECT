"""Read-only question bank: categories, conditions and questions with options."""

from __future__ import annotations

import uuid
from typing import Annotated, Optional, Sequence

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Condition, Question, TreatmentCategory
from app.models.enums import ClinicalDepartment, FlowType
from app.schemas.clinical import CategoryOut, ConditionOut, OptionOut, QuestionOut

router = APIRouter(prefix="/api", tags=["questionnaire"])


def question_to_out(question: Question) -> QuestionOut:
    """Serialise a question with its options in display order."""
    out = QuestionOut.model_validate(question)
    out.options = [
        OptionOut.model_validate(option)
        for option in sorted(question.options, key=lambda o: (o.display_order, o.label))
    ]
    return out


async def load_questions(db: AsyncSession, condition_id: uuid.UUID) -> Sequence[Question]:
    """Active questions for a condition, ordered, with options eagerly loaded."""
    result = await db.execute(
        select(Question)
        .where(Question.condition_id == condition_id, Question.is_active.is_(True))
        .options(selectinload(Question.options))
        .order_by(Question.display_order, Question.key)
    )
    return result.scalars().all()


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    flow_type: Annotated[Optional[FlowType], Query()] = None,
    department: Annotated[Optional[ClinicalDepartment], Query()] = None,
) -> list[CategoryOut]:
    stmt = (
        select(TreatmentCategory)
        .where(TreatmentCategory.is_active.is_(True))
        .order_by(TreatmentCategory.display_order, TreatmentCategory.name)
    )
    if flow_type is not None:
        stmt = stmt.where(TreatmentCategory.flow_type == flow_type.value)
    if department is not None:
        stmt = stmt.where(TreatmentCategory.department == department.value)

    rows = (await db.execute(stmt)).scalars().all()
    return [CategoryOut.model_validate(row) for row in rows]


@router.get("/conditions", response_model=list[ConditionOut])
async def list_conditions(
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: Annotated[Optional[uuid.UUID], Query()] = None,
) -> list[ConditionOut]:
    stmt = (
        select(Condition)
        .where(Condition.is_active.is_(True))
        .order_by(Condition.display_order, Condition.name)
    )
    if category_id is not None:
        stmt = stmt.where(Condition.category_id == category_id)

    rows = (await db.execute(stmt)).scalars().all()
    return [ConditionOut.model_validate(row) for row in rows]


@router.get("/questions", response_model=list[QuestionOut])
async def list_questions(
    db: Annotated[AsyncSession, Depends(get_db)],
    condition_id: Annotated[uuid.UUID, Query()],
) -> list[QuestionOut]:
    """
    The full question set for a condition.

    Returns every question, including ones only reachable through a branch, so
    admin tooling and previews can see the whole flow. Patients receive one
    question at a time from the session endpoints instead.
    """
    condition = await db.scalar(select(Condition).where(Condition.id == condition_id))
    if condition is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found.")

    questions = await load_questions(db, condition_id)
    return [question_to_out(q) for q in questions]
