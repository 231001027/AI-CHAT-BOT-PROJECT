"""
Tool implementations for the assistant suite.

Each handler is a deterministic database read (or a guarded write, for booking
and escalation). Handlers never call an LLM. They return plain dicts that the
runtime feeds back to the model as tool results, and that the offline fallback
formats directly.

Handlers must not raise for ordinary "nothing found" cases — they return a dict
with ``found: False`` so the model can respond gracefully instead of erroring.
"""

from __future__ import annotations

import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.scheduling_provider import BookingCommand, get_scheduling_provider
from app.models import (
    CounsellingResource,
    EscalationTicket,
    KnowledgeEntry,
    ScreeningProtocol,
    TestCatalog,
    TherapyGuideline,
)
from app.models.enums import (
    AgeBand,
    AgentType,
    EscalationPriority,
    EscalationStatus,
    TherapyDomain,
    Vertical,
)
from app.services.knowledge_base import KnowledgeSnapshot, rank_entries
from app.services.scheduling import SchedulingError, describe_slot

logger = logging.getLogger("nipmed.agents.tools")

# Departmental contact details live here, not in a prompt, so they cannot drift.
DEPARTMENT_CONTACT = {
    "phone": "044-2452-0639",
    "email": "care@niepmd.nic.in",
    "address": "NIEPMD, East Coast Road, Muttukadu, Kovalam Post, Chennai 603112",
    "working_hours": "Monday to Friday, 9:00 AM to 5:00 PM (closed on public holidays)",
}


# ---------------------------------------------------------------------------
# Knowledge base
# ---------------------------------------------------------------------------


async def search_knowledge_base(
    db: AsyncSession,
    query: str,
    agent_type: Optional[str] = None,
    vertical: Optional[str] = None,
    limit: int = 3,
) -> dict[str, Any]:
    """Deterministic keyword retrieval over clinician-authored entries."""
    rows = (
        (await db.execute(select(KnowledgeEntry).where(KnowledgeEntry.is_active.is_(True))))
        .scalars()
        .all()
    )
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
        query,
        snapshots,
        agent_type=agent_type,
        vertical=vertical,
        limit=max(1, min(limit, 5)),
    )
    if not hits:
        return {
            "found": False,
            "query": query,
            "message": "No departmental knowledge entry matched this question.",
            "contact": DEPARTMENT_CONTACT,
        }
    return {
        "found": True,
        "query": query,
        "results": [
            {
                "slug": h.entry.slug,
                "topic": h.entry.topic,
                "answer": h.entry.answer,
                "vertical": h.entry.vertical,
                "score": h.score,
            }
            for h in hits
        ],
    }


async def get_department_info(db: AsyncSession, topic: Optional[str] = None) -> dict[str, Any]:
    """Fixed contact/logistics facts. Deliberately not model-generated."""
    return {"found": True, "topic": topic or "contact", **DEPARTMENT_CONTACT}


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------


async def list_services(db: AsyncSession, vertical: Optional[str] = None) -> dict[str, Any]:
    provider = get_scheduling_provider(db)
    services = await provider.list_services(vertical=_valid_enum(vertical, Vertical))
    if not services:
        return {"found": False, "message": "No bookable services are configured."}
    return {
        "found": True,
        "provider": provider.name,
        "services": [
            {
                "code": s.code,
                "name": s.name,
                "vertical": s.vertical,
                "duration_minutes": s.duration_minutes,
                "description": s.description,
                "preparation": s.preparation,
                "documents_required": list(s.documents_required),
                "report_turnaround": s.report_turnaround,
            }
            for s in services
        ],
    }


async def find_available_slots(
    db: AsyncSession,
    service_code: Optional[str] = None,
    vertical: Optional[str] = None,
    days_ahead: int = 21,
    limit: int = 5,
) -> dict[str, Any]:
    provider = get_scheduling_provider(db)
    now = datetime.now(timezone.utc)
    try:
        slots = await provider.find_slots(
            service_code=service_code,
            vertical=_valid_enum(vertical, Vertical),
            earliest=now,
            latest=now + timedelta(days=max(1, min(days_ahead, 90))),
            limit=max(1, min(limit, 10)),
        )
    except SchedulingError as exc:
        return {"found": False, "error": exc.code, "message": exc.message}

    if not slots:
        return {
            "found": False,
            "message": (
                "No open slots in that window. Departmental staff can add a slot "
                "on request."
            ),
            "contact": DEPARTMENT_CONTACT,
        }
    return {
        "found": True,
        "provider": provider.name,
        "slots": [
            {
                "slot_id": s.slot_id,
                "service_code": s.service_code,
                "service_name": s.service_name,
                "starts_at": s.starts_at.isoformat(),
                "seats_left": s.seats_left,
                "clinician_name": s.clinician_name,
                "location": s.location,
                "human_readable": describe_slot(s),
            }
            for s in slots
        ],
    }


async def book_appointment(
    db: AsyncSession,
    slot_id: str,
    patient_name: str,
    phone: str,
    email: Optional[str] = None,
    notes: Optional[str] = None,
    conversation_id: Optional[str] = None,
    patient_id: Optional[str] = None,
) -> dict[str, Any]:
    """Confirm a slot. The only tool in the suite that writes a clinical booking."""
    provider = get_scheduling_provider(db)
    try:
        receipt = await provider.book(
            BookingCommand(
                slot_id=slot_id,
                patient_name=patient_name,
                phone=phone,
                email=email,
                notes=notes,
                conversation_id=conversation_id,
                patient_id=patient_id,
            )
        )
    except SchedulingError as exc:
        return {"booked": False, "error": exc.code, "message": exc.message}
    return {"booked": True, "appointment": receipt.as_dict()}


async def lookup_appointment(db: AsyncSession, reference_code: str) -> dict[str, Any]:
    provider = get_scheduling_provider(db)
    try:
        receipt = await provider.lookup(reference_code)
    except SchedulingError as exc:
        return {"found": False, "error": exc.code, "message": exc.message}
    if receipt is None:
        return {
            "found": False,
            "message": f"No appointment found for reference {reference_code}.",
        }
    return {"found": True, "appointment": receipt.as_dict()}


async def cancel_appointment(db: AsyncSession, reference_code: str) -> dict[str, Any]:
    provider = get_scheduling_provider(db)
    try:
        receipt = await provider.cancel(reference_code)
    except SchedulingError as exc:
        return {"cancelled": False, "error": exc.code, "message": exc.message}
    return {"cancelled": True, "appointment": receipt.as_dict()}


async def reschedule_appointment(
    db: AsyncSession, reference_code: str, new_slot_id: str
) -> dict[str, Any]:
    provider = get_scheduling_provider(db)
    try:
        receipt = await provider.reschedule(reference_code, new_slot_id)
    except SchedulingError as exc:
        return {"rescheduled": False, "error": exc.code, "message": exc.message}
    return {"rescheduled": True, "appointment": receipt.as_dict()}


# ---------------------------------------------------------------------------
# Hearing screening (Audiology)
# ---------------------------------------------------------------------------


async def get_screening_protocol(db: AsyncSession, age_band: str) -> dict[str, Any]:
    band = _valid_enum(age_band, AgeBand)
    if band is None:
        return {
            "found": False,
            "message": f"'{age_band}' is not a recognised age band.",
            "valid_age_bands": [b.value for b in AgeBand],
        }
    row = (
        await db.execute(select(ScreeningProtocol).where(ScreeningProtocol.age_band == band))
    ).scalar_one_or_none()
    if row is None:
        return {"found": False, "message": f"No screening protocol configured for {band}."}

    tests = await _describe_tests(db, row.test_codes or [])
    return {
        "found": True,
        "age_band": row.age_band,
        "name": row.name,
        "summary": row.summary,
        "tests": tests,
        "referral_criteria": list(row.referral_criteria or []),
        "timeline": row.timeline,
        "preparation": row.preparation,
    }


async def list_screening_protocols(db: AsyncSession) -> dict[str, Any]:
    rows = (
        (await db.execute(select(ScreeningProtocol).order_by(ScreeningProtocol.age_band)))
        .scalars()
        .all()
    )
    if not rows:
        return {"found": False, "message": "No screening protocols are configured."}
    return {
        "found": True,
        "protocols": [
            {
                "age_band": r.age_band,
                "name": r.name,
                "summary": r.summary,
                "timeline": r.timeline,
                "test_codes": list(r.test_codes or []),
            }
            for r in rows
        ],
    }


async def get_test_info(db: AsyncSession, code: str) -> dict[str, Any]:
    row = (
        await db.execute(select(TestCatalog).where(TestCatalog.code.ilike(code)))
    ).scalar_one_or_none()
    if row is None:
        return {"found": False, "message": f"No test named '{code}' is in the catalogue."}
    return {
        "found": True,
        "code": row.code,
        "name": row.name,
        "category": row.category,
        "description": row.description,
    }


# ---------------------------------------------------------------------------
# Speech-Language Pathology
# ---------------------------------------------------------------------------


async def get_therapy_guideline(
    db: AsyncSession, domain: str, age_band: Optional[str] = None
) -> dict[str, Any]:
    parsed_domain = _valid_enum(domain, TherapyDomain)
    if parsed_domain is None:
        return {
            "found": False,
            "message": f"'{domain}' is not a recognised therapy domain.",
            "valid_domains": [d.value for d in TherapyDomain],
        }

    stmt = select(TherapyGuideline).where(TherapyGuideline.domain == parsed_domain)
    band = _valid_enum(age_band, AgeBand)
    if band:
        stmt = stmt.where(TherapyGuideline.age_band == band)
    rows = (await db.execute(stmt)).scalars().all()

    if not rows and band:
        # Fall back to the domain-wide guideline when the band has no specific one.
        rows = (
            (
                await db.execute(
                    select(TherapyGuideline).where(
                        TherapyGuideline.domain == parsed_domain,
                        TherapyGuideline.age_band.is_(None),
                    )
                )
            )
            .scalars()
            .all()
        )
    if not rows:
        return {"found": False, "message": f"No guideline configured for {parsed_domain}."}

    return {
        "found": True,
        "guidelines": [
            {
                "domain": r.domain,
                "age_band": r.age_band,
                "title": r.title,
                "summary": r.summary,
                "milestones": list(r.milestones or []),
                "home_activities": list(r.home_activities or []),
                "red_flags": list(r.red_flags or []),
                "typical_frequency": r.typical_frequency,
            }
            for r in rows
        ],
    }


async def list_therapy_domains(db: AsyncSession) -> dict[str, Any]:
    rows = (
        (await db.execute(select(TherapyGuideline).order_by(TherapyGuideline.domain)))
        .scalars()
        .all()
    )
    seen: dict[str, dict[str, Any]] = {}
    for r in rows:
        entry = seen.setdefault(r.domain, {"domain": r.domain, "titles": [], "age_bands": []})
        entry["titles"].append(r.title)
        if r.age_band:
            entry["age_bands"].append(r.age_band)
    if not seen:
        return {"found": False, "message": "No therapy guidelines are configured."}
    return {"found": True, "domains": list(seen.values())}


# ---------------------------------------------------------------------------
# Parent counselling (Early Intervention)
# ---------------------------------------------------------------------------


async def get_counselling_resources(
    db: AsyncSession, query: Optional[str] = None, age_band: Optional[str] = None, limit: int = 3
) -> dict[str, Any]:
    stmt = select(CounsellingResource)
    band = _valid_enum(age_band, AgeBand)
    if band:
        stmt = stmt.where(CounsellingResource.age_band == band)
    rows = (await db.execute(stmt)).scalars().all()

    if not rows and band:
        rows = (await db.execute(select(CounsellingResource))).scalars().all()
    if not rows:
        return {"found": False, "message": "No counselling resources are configured."}

    if query:
        # Reuse the knowledge scorer so ranking behaves identically everywhere.
        snapshots = [
            KnowledgeSnapshot(
                slug=r.slug,
                vertical=Vertical.EARLY_INTERVENTION.value,
                agent_types=(AgentType.COUNSELLING.value,),
                topic=r.topic,
                question=r.topic,
                answer=r.summary,
                keywords=tuple(r.keywords or ()),
            )
            for r in rows
        ]
        ranked = rank_entries(
            query,
            snapshots,
            agent_type=AgentType.COUNSELLING.value,
            limit=max(1, min(limit, 5)),
            min_score=0.2,
        )
        if ranked:
            wanted = {h.entry.slug for h in ranked}
            rows = [r for r in rows if r.slug in wanted]

    selected = rows[: max(1, min(limit, 5))]
    return {
        "found": True,
        "resources": [
            {
                "slug": r.slug,
                "topic": r.topic,
                "age_band": r.age_band,
                "summary": r.summary,
                "talking_points": list(r.talking_points or []),
                "reassurance": list(r.reassurance or []),
                "next_steps": list(r.next_steps or []),
            }
            for r in selected
        ],
    }


# ---------------------------------------------------------------------------
# Human hand-off
# ---------------------------------------------------------------------------


async def escalate_to_staff(
    db: AsyncSession,
    reason: str,
    priority: str = "routine",
    agent_type: Optional[str] = None,
    vertical: Optional[str] = None,
    contact_name: Optional[str] = None,
    contact_phone: Optional[str] = None,
    conversation_id: Optional[str] = None,
    triggers: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Create a ticket for departmental staff and tell the user what happens next."""
    parsed_priority = _valid_enum(priority, EscalationPriority) or EscalationPriority.ROUTINE
    ticket = EscalationTicket(
        reference_code=_ticket_reference(),
        conversation_id=uuid.UUID(conversation_id) if conversation_id else None,
        agent_type=agent_type or AgentType.ENQUIRY.value,
        vertical=_valid_enum(vertical, Vertical) or Vertical.DEPARTMENT.value,
        reason=reason,
        priority=parsed_priority,
        status=EscalationStatus.OPEN.value,
        contact_name=contact_name,
        contact_phone=contact_phone,
        triggers=triggers or None,
    )
    db.add(ticket)
    await db.flush()
    return {
        "escalated": True,
        "reference_code": ticket.reference_code,
        "priority": ticket.priority,
        "message": (
            "Departmental staff have been notified and will follow up. "
            f"Your reference is {ticket.reference_code}."
        ),
        "contact": DEPARTMENT_CONTACT,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _ticket_reference() -> str:
    body = "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    return f"ESC-{body}"


def _valid_enum(value: Optional[str], enum_cls: Any) -> Optional[str]:
    """Coerce a model-supplied string to a known enum value, or None."""
    if not value:
        return None
    try:
        return enum_cls(value).value
    except ValueError:
        logger.debug("Discarding unknown %s value %r", enum_cls.__name__, value)
        return None


async def _describe_tests(db: AsyncSession, codes: list[str]) -> list[dict[str, str]]:
    if not codes:
        return []
    rows = (await db.execute(select(TestCatalog).where(TestCatalog.code.in_(codes)))).scalars().all()
    by_code = {r.code: r for r in rows}
    described: list[dict[str, str]] = []
    for code in codes:
        row = by_code.get(code)
        described.append(
            {
                "code": code,
                "name": row.name if row else code,
                "description": row.description if row else "",
            }
        )
    return described
