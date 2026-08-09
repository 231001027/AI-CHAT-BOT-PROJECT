"""Test recommendation (rules engine) and special-test detail."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import cache_session_state
from app.db.session import get_db
from app.models import ChatSession, Concern, ConcernConfig, SymptomResponse, TestCatalog
from app.models.enums import AgeBand, ConcernType, SessionStep
from app.schemas import RecommendTestsResponse, RecommendedTestOut, TestDetailOut
from app.services import state_machine as sm
from app.services.rules_engine import (
    CatalogEntry,
    ConcernConfigSnapshot,
    enrich_with_catalog,
    general_recommendations_for,
    recommend_tests,
)

router = APIRouter(prefix="/api/tests", tags=["Tests"])


@router.get("/recommend/{concern_id}", response_model=RecommendTestsResponse)
async def recommend_for_concern(concern_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Deterministic recommendations from ConcernConfig + symptom answers.
    NO LLM involvement.
    """
    concern = await db.get(Concern, concern_id)
    if not concern:
        raise HTTPException(status_code=404, detail="Concern not found")

    stmt = select(ConcernConfig).where(ConcernConfig.concern_type == concern.concern_type)
    if concern.age_band:
        stmt = stmt.where(ConcernConfig.age_band == concern.age_band)
    else:
        stmt = stmt.where(ConcernConfig.age_band.is_(None))
    config_row = (await db.execute(stmt)).scalar_one_or_none()
    if not config_row:
        raise HTTPException(status_code=404, detail="ConcernConfig not found")

    answers_rows = (
        await db.execute(select(SymptomResponse).where(SymptomResponse.concern_id == concern_id))
    ).scalars().all()
    answers = {r.question_key: r.answer for r in answers_rows}

    snapshot = ConcernConfigSnapshot(
        concern_type=config_row.concern_type,
        age_band=config_row.age_band,
        recommended_tests=list(config_row.recommended_tests or []),
        what_it_helps=config_row.what_it_helps,
        outcome_options=list(config_row.outcome_options) if config_row.outcome_options else None,
        conditional_rules=list(config_row.conditional_rules) if config_row.conditional_rules else None,
    )
    result = recommend_tests(snapshot, answers)

    catalog_rows = (await db.execute(select(TestCatalog))).scalars().all()
    catalog = {
        t.code: CatalogEntry(code=t.code, name=t.name, category=t.category, description=t.description)
        for t in catalog_rows
    }
    enriched = enrich_with_catalog(result, catalog)

    # Advance session to recommendations if we can find it
    session_stmt = select(ChatSession).where(ChatSession.patient_id == concern.patient_id)
    sessions = (await db.execute(session_stmt)).scalars().all()
    for session in sessions:
        ctx = session.context or {}
        if ctx.get("active_concern_id") == str(concern_id):
            current = sm.parse_step(session.current_step)
            if current == SessionStep.SYMPTOMS:
                session.current_step = SessionStep.RECOMMENDATIONS.value
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
            break

    return RecommendTestsResponse(
        concern_id=concern_id,
        concern_type=ConcernType(concern.concern_type),
        age_band=AgeBand(concern.age_band) if concern.age_band else None,
        tests=[RecommendedTestOut(**t) for t in enriched],
        what_it_helps=result.what_it_helps,
        outcome_options=result.outcome_options,
        general_recommendations=general_recommendations_for(
            concern.concern_type, concern.age_band
        ),
    )


@router.get("/special/{code}", response_model=TestDetailOut)
async def get_special_test(code: str, db: AsyncSession = Depends(get_db)):
    row = (
        await db.execute(select(TestCatalog).where(TestCatalog.code == code))
    ).scalar_one_or_none()
    if not row:
        # try case-insensitive
        row = (
            await db.execute(select(TestCatalog).where(TestCatalog.code.ilike(code)))
        ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail=f"Test not found: {code}")
    return TestDetailOut(
        code=row.code,
        name=row.name,
        category=row.category,
        description=row.description,
    )


@router.get("", response_model=list[TestDetailOut])
async def list_tests(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(TestCatalog).order_by(TestCatalog.code))).scalars().all()
    return [
        TestDetailOut(code=r.code, name=r.name, category=r.category, description=r.description)
        for r in rows
    ]
