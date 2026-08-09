"""
Direct scheduling API.

The same provider the scheduling assistant uses, exposed for the booking UI so a
patient who would rather click than chat gets identical availability and rules.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.scheduling_provider import BookingCommand, get_scheduling_provider
from app.models.enums import Vertical
from app.schemas.agents import (
    AppointmentOut,
    CreateAppointmentRequest,
    RescheduleRequest,
    ServiceOut,
    SlotOut,
)
from app.services.scheduling import SchedulingError, describe_slot

router = APIRouter(prefix="/api/scheduling", tags=["Scheduling"])


@router.get("/services", response_model=list[ServiceOut])
async def list_services(
    vertical: Optional[Vertical] = None, db: AsyncSession = Depends(get_db)
):
    provider = get_scheduling_provider(db)
    services = await provider.list_services(vertical=vertical.value if vertical else None)
    return [
        ServiceOut(
            code=s.code,
            name=s.name,
            vertical=Vertical(s.vertical),
            duration_minutes=s.duration_minutes,
            description=s.description,
            preparation=s.preparation,
            documents_required=list(s.documents_required),
            report_turnaround=s.report_turnaround,
        )
        for s in services
    ]


@router.get("/slots", response_model=list[SlotOut])
async def list_slots(
    service_code: Optional[str] = None,
    vertical: Optional[Vertical] = None,
    days_ahead: int = Query(default=21, ge=1, le=90),
    limit: int = Query(default=10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    try:
        slots = await get_scheduling_provider(db).find_slots(
            service_code=service_code,
            vertical=vertical.value if vertical else None,
            earliest=now,
            latest=now + timedelta(days=days_ahead),
            limit=limit,
        )
    except SchedulingError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc

    return [
        SlotOut(
            slot_id=s.slot_id,
            service_code=s.service_code,
            service_name=s.service_name,
            starts_at=s.starts_at,
            ends_at=s.ends_at,
            seats_left=s.seats_left,
            clinician_name=s.clinician_name,
            location=s.location,
            human_readable=describe_slot(s),
        )
        for s in slots
    ]


@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    payload: CreateAppointmentRequest, db: AsyncSession = Depends(get_db)
):
    try:
        receipt = await get_scheduling_provider(db).book(
            BookingCommand(
                slot_id=payload.slot_id,
                patient_name=payload.patient_name,
                phone=payload.phone,
                email=str(payload.email) if payload.email else None,
                notes=payload.notes,
                conversation_id=str(payload.conversation_id) if payload.conversation_id else None,
                patient_id=str(payload.patient_id) if payload.patient_id else None,
            )
        )
    except SchedulingError as exc:
        raise HTTPException(status_code=409, detail=exc.message) from exc

    await db.commit()
    return AppointmentOut(**receipt.as_dict())


@router.get("/appointments/{reference_code}", response_model=AppointmentOut)
async def get_appointment(reference_code: str, db: AsyncSession = Depends(get_db)):
    try:
        receipt = await get_scheduling_provider(db).lookup(reference_code)
    except SchedulingError as exc:
        raise HTTPException(status_code=502, detail=exc.message) from exc
    if receipt is None:
        raise HTTPException(status_code=404, detail=f"No appointment found for {reference_code}")
    return AppointmentOut(**receipt.as_dict())


@router.post("/appointments/{reference_code}/cancel", response_model=AppointmentOut)
async def cancel_appointment(reference_code: str, db: AsyncSession = Depends(get_db)):
    try:
        receipt = await get_scheduling_provider(db).cancel(reference_code)
    except SchedulingError as exc:
        status = 404 if exc.code == "not_found" else 409
        raise HTTPException(status_code=status, detail=exc.message) from exc
    await db.commit()
    return AppointmentOut(**receipt.as_dict())


@router.post("/appointments/{reference_code}/reschedule", response_model=AppointmentOut)
async def reschedule_appointment(
    reference_code: str, payload: RescheduleRequest, db: AsyncSession = Depends(get_db)
):
    try:
        receipt = await get_scheduling_provider(db).reschedule(reference_code, payload.new_slot_id)
    except SchedulingError as exc:
        status = 404 if exc.code == "not_found" else 409
        raise HTTPException(status_code=status, detail=exc.message) from exc
    await db.commit()
    return AppointmentOut(**receipt.as_dict())
