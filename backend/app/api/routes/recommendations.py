"""
Recommendation engine endpoints.

Evaluates admin-authored clinical rules against a completed questionnaire. No
LLM is involved at any point on this path — it is the clinically essential route
and must stay deterministic and available.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import (
    ClinicalRule,
    Patient,
    PatientAnswer,
    PatientProfile,
    QuestionnaireSession,
    TestCatalog,
    TreatmentPlan,
)
from app.schemas.clinical import (
    EvaluateRequest,
    RecommendationOut,
    RecommendedTestOut,
)
from app.services.clinical_rules import (
    RuleSnapshot,
    TestRecommendation,
    build_facts,
    general_recommendations_for,
    recommend_tests,
)

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


async def _load_rules(
    db: AsyncSession, *, condition_id: Optional[uuid.UUID], category_id: Optional[uuid.UUID]
) -> list[RuleSnapshot]:
    """
    Active rules applicable to this session.

    A rule scoped to the condition applies, as does one scoped to the category
    with no condition (so shared rules do not have to be duplicated per
    condition).
    """
    scopes = []
    if condition_id is not None:
        scopes.append(ClinicalRule.condition_id == condition_id)
    if category_id is not None:
        scopes.append(
            (ClinicalRule.category_id == category_id) & ClinicalRule.condition_id.is_(None)
        )
    if not scopes:
        return []

    rows = (
        await db.execute(
            select(ClinicalRule)
            .where(ClinicalRule.is_active.is_(True), or_(*scopes))
            .options(selectinload(ClinicalRule.tests))
            .order_by(ClinicalRule.priority.desc(), ClinicalRule.name)
        )
    ).scalars().all()

    return [
        RuleSnapshot(
            rule_id=str(rule.id),
            name=rule.name,
            rule_definition=rule.rule_definition or {},
            priority=rule.priority,
            is_baseline=rule.is_baseline,
            condition_id=str(rule.condition_id) if rule.condition_id else None,
            tests=tuple(
                TestRecommendation(
                    test_code=t.test_code,
                    test_name=t.test_name,
                    reason_text=t.reason_text,
                    rule_name=rule.name,
                    priority=rule.priority,
                    display_order=t.display_order,
                )
                for t in rule.tests
            ),
        )
        for rule in rows
    ]


async def _enrich(db: AsyncSession, tests: list[TestRecommendation]) -> list[RecommendedTestOut]:
    """Attach catalogue detail (description, preparation) where the code matches."""
    if not tests:
        return []

    codes = [t.test_code.upper() for t in tests]
    catalog = (
        await db.execute(select(TestCatalog).where(TestCatalog.code.in_(codes)))
    ).scalars().all()
    by_code = {c.code.upper(): c for c in catalog}

    enriched: list[RecommendedTestOut] = []
    for test in tests:
        entry = by_code.get(test.test_code.upper())
        enriched.append(
            RecommendedTestOut(
                test_code=test.test_code,
                test_name=test.test_name or (entry.name if entry else test.test_code),
                reason_text=test.reason_text,
                rule_name=test.rule_name,
                description=entry.description if entry else None,
                preparation=entry.preparation if entry else None,
                duration_minutes=entry.duration_minutes if entry else None,
            )
        )
    return enriched


async def _build_plan(db: AsyncSession, session: QuestionnaireSession) -> TreatmentPlan:
    """Run the rules for a session and persist an immutable plan snapshot."""
    patient = await db.scalar(select(Patient).where(Patient.id == session.patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    profile = await db.scalar(
        select(PatientProfile)
        .where(PatientProfile.patient_id == patient.id)
        .order_by(PatientProfile.created_at.desc())
    )

    answers = (
        await db.execute(select(PatientAnswer).where(PatientAnswer.session_id == session.id))
    ).scalars().all()
    if not answers:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No answers have been recorded for this session yet.",
        )

    facts = build_facts(
        age=patient.age,
        gender=patient.gender,
        district=patient.district,
        flow_type=profile.flow_type if profile else None,
        child_subtype=profile.child_subtype if profile else None,
        answers={a.question_key: a.answer_value for a in answers},
    )

    rules = await _load_rules(
        db, condition_id=session.condition_id, category_id=session.category_id
    )
    outcome = recommend_tests(
        rules,
        facts,
        general_recommendations=general_recommendations_for(
            profile.flow_type if profile else None
        ),
    )

    plan = TreatmentPlan(
        patient_id=patient.id,
        session_id=session.id,
        recommended_tests=[
            {
                "test_code": t.test_code,
                "test_name": t.test_name,
                "reason_text": t.reason_text,
                "rule_name": t.rule_name,
            }
            for t in outcome.tests
        ],
        matched_rule_ids=list(outcome.matched_rule_ids),
        general_recommendations=list(outcome.general_recommendations),
    )
    db.add(plan)
    await db.flush()
    return plan


def _plan_to_out(plan: TreatmentPlan, tests: list[RecommendedTestOut]) -> RecommendationOut:
    return RecommendationOut(
        session_id=plan.session_id,
        plan_id=plan.id,
        recommended_tests=tests,
        general_recommendations=list(plan.general_recommendations or []),
        matched_rule_ids=[uuid.UUID(r) for r in (plan.matched_rule_ids or [])],
        generated_at=plan.generated_at,
    )


@router.post("/evaluate", response_model=RecommendationOut)
async def evaluate(
    payload: EvaluateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationOut:
    """Evaluate the rules for a session and store the resulting plan."""
    session = await db.scalar(
        select(QuestionnaireSession).where(QuestionnaireSession.id == payload.session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    plan = await _build_plan(db, session)
    tests = await _enrich(
        db,
        [
            TestRecommendation(
                test_code=t.get("test_code", ""),
                test_name=t.get("test_name", ""),
                reason_text=t.get("reason_text", ""),
                rule_name=t.get("rule_name", ""),
            )
            for t in plan.recommended_tests
        ],
    )
    return _plan_to_out(plan, tests)


@router.get("/{session_id}", response_model=RecommendationOut)
async def get_recommendations(
    session_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RecommendationOut:
    """
    The most recent plan for a session.

    Reads the stored snapshot rather than re-evaluating, so a report and the
    screen it was generated from can never disagree.
    """
    plan = await db.scalar(
        select(TreatmentPlan)
        .where(TreatmentPlan.session_id == session_id)
        .order_by(TreatmentPlan.generated_at.desc())
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No recommendations have been generated for this session yet.",
        )

    tests = await _enrich(
        db,
        [
            TestRecommendation(
                test_code=t.get("test_code", ""),
                test_name=t.get("test_name", ""),
                reason_text=t.get("reason_text", ""),
                rule_name=t.get("rule_name", ""),
            )
            for t in plan.recommended_tests
        ],
    )
    return _plan_to_out(plan, tests)
