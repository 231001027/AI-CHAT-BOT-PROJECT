"""Concern config fetch + select concern for a session."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import cache_session_state
from app.db.session import get_db
from app.models import ChatSession, Concern, ConcernConfig
from app.models.enums import AgeBand, ConcernType, SessionStatus, SessionStep
from app.schemas import (
    CommonSignOut,
    ConcernConfigOut,
    SelectConcernRequest,
    SelectConcernResponse,
)
from app.services import state_machine as sm

router = APIRouter(prefix="/api/concerns", tags=["Concerns"])


def _to_out(row: ConcernConfig) -> ConcernConfigOut:
    signs = [
        CommonSignOut(key=s.get("key", f"q{i}"), prompt=s.get("prompt", ""))
        for i, s in enumerate(row.common_signs or [])
    ]
    return ConcernConfigOut(
        concern_type=ConcernType(row.concern_type),
        age_band=AgeBand(row.age_band) if row.age_band else None,
        common_signs=signs,
        recommended_tests=list(row.recommended_tests or []),
        what_it_helps=row.what_it_helps,
        outcome_options=list(row.outcome_options) if row.outcome_options else None,
    )


async def _load_config(
    db: AsyncSession,
    concern_type: ConcernType,
    age_band: Optional[AgeBand],
) -> ConcernConfig:
    stmt = select(ConcernConfig).where(ConcernConfig.concern_type == concern_type.value)
    if age_band is not None:
        stmt = stmt.where(ConcernConfig.age_band == age_band.value)
    else:
        stmt = stmt.where(ConcernConfig.age_band.is_(None))
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()
    if not row:
        raise HTTPException(
            status_code=404,
            detail=f"No ConcernConfig for {concern_type.value}"
            + (f" / {age_band.value}" if age_band else ""),
        )
    return row


@router.get("/{concern_type}", response_model=ConcernConfigOut)
async def get_concern_config(
    concern_type: ConcernType,
    age_band: Optional[AgeBand] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Fetch config (signs, tests, explanation). Pass age_band for child pathways."""
    row = await _load_config(db, concern_type, age_band)
    return _to_out(row)


@router.post("/select", response_model=SelectConcernResponse)
async def select_concern(body: SelectConcernRequest, db: AsyncSession = Depends(get_db)):
    """Attach a concern to the patient/session and advance to symptoms step."""
    session = await db.get(ChatSession, body.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status != SessionStatus.ACTIVE.value:
        raise HTTPException(status_code=409, detail="Session is not active")
    if not session.patient_id:
        raise HTTPException(status_code=400, detail="Profile must be saved before selecting a concern")

    current = sm.parse_step(session.current_step)
    sm.assert_step(current, {SessionStep.CONCERN_SELECT, SessionStep.SYMPTOMS}, "select_concern")

    age_band = body.age_band
    if body.concern_type == ConcernType.CHILD_CONCERNS and age_band is None:
        # Prefer suggested band from profile age
        ctx = session.context or {}
        if ctx.get("suggested_age_band"):
            age_band = AgeBand(ctx["suggested_age_band"])

    config = await _load_config(db, body.concern_type, age_band)
    source = sm.source_page_for_concern(body.concern_type, age_band)

    concern = Concern(
        patient_id=session.patient_id,
        concern_type=body.concern_type.value,
        source_page=source,
        age_band=age_band.value if age_band else None,
    )
    db.add(concern)
    await db.flush()

    ctx = dict(session.context or {})
    ctx["active_concern_id"] = str(concern.id)
    ctx["concern_type"] = body.concern_type.value
    if age_band:
        ctx["age_band"] = age_band.value
    session.context = ctx
    session.current_step = sm.next_after_concern_selected().value
    await db.flush()

    await cache_session_state(
        str(session.id),
        {
            "current_step": session.current_step,
            "status": session.status,
            "patient_id": str(session.patient_id),
            "context": session.context,
        },
    )

    return SelectConcernResponse(
        session_id=session.id,
        concern_id=concern.id,
        concern_type=body.concern_type,
        age_band=age_band,
        source_page=source,
        current_step=SessionStep.SYMPTOMS,
        config=_to_out(config),
    )
