"""
Read-only clinical content APIs.

Screening protocols, therapy guidelines, counselling resources and knowledge
search. These back the informational pages of the portal and are the same rows
the assistants read, so chat and pages can never disagree.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import CounsellingResource, KnowledgeEntry, ScreeningProtocol, TherapyGuideline
from app.models.enums import AgeBand, AgentType, TherapyDomain, Vertical
from app.schemas.agents import (
    CounsellingResourceOut,
    KnowledgeHitOut,
    KnowledgeSearchResponse,
    ScreeningProtocolOut,
    TherapyGuidelineOut,
)
from app.services.knowledge_base import KnowledgeSnapshot, rank_entries

router = APIRouter(prefix="/api", tags=["Guidance"])


@router.get("/knowledge/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    q: str = Query(min_length=2, max_length=500),
    agent_id: Optional[AgentType] = None,
    vertical: Optional[Vertical] = None,
    limit: int = Query(default=5, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    rows = (
        (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.is_active.is_(True))))
        .scalars()
        .all()
    )
    by_slug = {r.slug: r for r in rows}
    snapshots = [
        KnowledgeSnapshot(
            slug=r.slug,
            vertical=r.vertical,
            agent_types=tuple(r.agent_types or ()),
            topic=r.topic,
            question=r.question,
            answer=r.answer,
            keywords=tuple(r.keywords or ()),
            priority=r.priority,
        )
        for r in rows
    ]
    hits = rank_entries(
        q,
        snapshots,
        agent_type=agent_id.value if agent_id else None,
        vertical=vertical.value if vertical else None,
        limit=limit,
    )
    return KnowledgeSearchResponse(
        query=q,
        results=[
            KnowledgeHitOut(
                slug=h.entry.slug,
                topic=h.entry.topic,
                question=by_slug[h.entry.slug].question,
                answer=h.entry.answer,
                vertical=Vertical(h.entry.vertical),
                score=h.score,
            )
            for h in hits
        ],
    )


@router.get("/screening/protocols", response_model=list[ScreeningProtocolOut])
async def list_screening_protocols(db: AsyncSession = Depends(get_db)):
    rows = (
        (await db.execute(select(ScreeningProtocol).order_by(ScreeningProtocol.age_band)))
        .scalars()
        .all()
    )
    return [_protocol_out(r) for r in rows]


@router.get("/screening/protocols/{age_band}", response_model=ScreeningProtocolOut)
async def get_screening_protocol(age_band: AgeBand, db: AsyncSession = Depends(get_db)):
    row = (
        await db.execute(
            select(ScreeningProtocol).where(ScreeningProtocol.age_band == age_band.value)
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No protocol for {age_band.value}")
    return _protocol_out(row)


@router.get("/slp/guidelines", response_model=list[TherapyGuidelineOut])
async def list_therapy_guidelines(
    domain: Optional[TherapyDomain] = None,
    age_band: Optional[AgeBand] = None,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(TherapyGuideline)
    if domain:
        stmt = stmt.where(TherapyGuideline.domain == domain.value)
    if age_band:
        stmt = stmt.where(TherapyGuideline.age_band == age_band.value)
    rows = (
        (await db.execute(stmt.order_by(TherapyGuideline.domain, TherapyGuideline.age_band)))
        .scalars()
        .all()
    )
    return [
        TherapyGuidelineOut(
            domain=TherapyDomain(r.domain),
            age_band=AgeBand(r.age_band) if r.age_band else None,
            title=r.title,
            summary=r.summary,
            milestones=list(r.milestones or []),
            home_activities=list(r.home_activities or []),
            red_flags=list(r.red_flags or []),
            typical_frequency=r.typical_frequency,
        )
        for r in rows
    ]


@router.get("/counselling/resources", response_model=list[CounsellingResourceOut])
async def list_counselling_resources(
    age_band: Optional[AgeBand] = None, db: AsyncSession = Depends(get_db)
):
    stmt = select(CounsellingResource)
    if age_band:
        stmt = stmt.where(CounsellingResource.age_band == age_band.value)
    rows = (await db.execute(stmt.order_by(CounsellingResource.topic))).scalars().all()
    return [
        CounsellingResourceOut(
            slug=r.slug,
            topic=r.topic,
            age_band=AgeBand(r.age_band) if r.age_band else None,
            summary=r.summary,
            talking_points=list(r.talking_points or []),
            reassurance=list(r.reassurance or []),
            next_steps=list(r.next_steps or []),
        )
        for r in rows
    ]


def _protocol_out(row: ScreeningProtocol) -> ScreeningProtocolOut:
    return ScreeningProtocolOut(
        age_band=AgeBand(row.age_band),
        name=row.name,
        summary=row.summary,
        test_codes=list(row.test_codes or []),
        referral_criteria=list(row.referral_criteria or []),
        timeline=row.timeline,
        preparation=row.preparation,
    )
