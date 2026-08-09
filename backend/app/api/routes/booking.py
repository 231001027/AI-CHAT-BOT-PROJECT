"""Appointment / contact booking capture."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import BookingRequest, ChatSession
from app.models.enums import SessionStep, SessionStatus
from app.schemas import BookingRequestIn, BookingResponse
from app.services import state_machine as sm

router = APIRouter(prefix="/api", tags=["Booking"])


@router.post("/booking", response_model=BookingResponse, status_code=201)
async def create_booking(body: BookingRequestIn, db: AsyncSession = Depends(get_db)):
    patient_id = None
    if body.session_id:
        session = await db.get(ChatSession, body.session_id)
        if session:
            patient_id = session.patient_id
            current = sm.parse_step(session.current_step)
            if current in {SessionStep.RECOMMENDATIONS, SessionStep.BOOKING, SessionStep.COMPLETE}:
                session.current_step = SessionStep.COMPLETE.value
                session.status = SessionStatus.COMPLETED.value

    row = BookingRequest(
        session_id=body.session_id,
        patient_id=patient_id,
        name=body.name,
        phone=body.phone,
        email=str(body.email) if body.email else None,
        preferred_slot=body.preferred_slot,
        notes=body.notes,
    )
    db.add(row)
    await db.flush()

    return BookingResponse(
        id=row.id,
        status="received",
        message="Thank you. Our team will contact you to confirm your appointment.",
        created_at=row.created_at,
    )
