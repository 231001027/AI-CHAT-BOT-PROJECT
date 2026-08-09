"""
Scheduling integration boundary.

The department may already run its own HIS/HMIS. Rather than assume either way,
every scheduling action goes through this interface:

* ``LocalSchedulingProvider`` — our own ``appointment_slots`` tables. Default,
  needs no external dependency, and is what the seed data populates.
* ``HttpSchedulingProvider`` — forwards the same operations to an existing REST
  API. Point ``SCHEDULING_API_BASE_URL`` at it and set
  ``SCHEDULING_PROVIDER=http``; no agent or route code changes.

Both return the same dataclasses, so the scheduling assistant is unaware of
which system of record is behind it.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional, Protocol, runtime_checkable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Appointment, AppointmentSlot, Clinician, Service
from app.models.enums import AppointmentStatus, SlotStatus
from app.services.scheduling import (
    SchedulingError,
    SlotSnapshot,
    assert_bookable,
    can_cancel,
    can_reschedule,
    filter_slots,
    generate_reference_code,
)

logger = logging.getLogger("nipmed.scheduling")


@dataclass(frozen=True)
class ServiceInfo:
    code: str
    name: str
    vertical: str
    duration_minutes: int
    description: str
    preparation: Optional[str] = None
    documents_required: tuple[str, ...] = ()
    report_turnaround: Optional[str] = None


@dataclass(frozen=True)
class BookingCommand:
    slot_id: str
    patient_name: str
    phone: str
    email: Optional[str] = None
    notes: Optional[str] = None
    conversation_id: Optional[str] = None
    patient_id: Optional[str] = None


@dataclass(frozen=True)
class BookingReceipt:
    reference_code: str
    status: str
    service_name: str
    starts_at: Optional[datetime]
    patient_name: str
    phone: str
    clinician_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "reference_code": self.reference_code,
            "status": self.status,
            "service_name": self.service_name,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "patient_name": self.patient_name,
            "phone": self.phone,
            "clinician_name": self.clinician_name,
            "location": self.location,
            "notes": self.notes,
        }


@runtime_checkable
class SchedulingProvider(Protocol):
    """Operations the scheduling assistant needs from a system of record."""

    name: str

    async def list_services(self, vertical: Optional[str] = None) -> list[ServiceInfo]: ...

    async def find_slots(
        self,
        *,
        service_code: Optional[str] = None,
        vertical: Optional[str] = None,
        earliest: Optional[datetime] = None,
        latest: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[SlotSnapshot]: ...

    async def book(self, command: BookingCommand) -> BookingReceipt: ...

    async def lookup(self, reference_code: str) -> Optional[BookingReceipt]: ...

    async def cancel(self, reference_code: str) -> BookingReceipt: ...

    async def reschedule(self, reference_code: str, new_slot_id: str) -> BookingReceipt: ...


class LocalSchedulingProvider:
    """DB-backed provider over our own slot tables."""

    name = "local"

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_services(self, vertical: Optional[str] = None) -> list[ServiceInfo]:
        stmt = select(Service).where(Service.is_active.is_(True))
        if vertical:
            stmt = stmt.where(Service.vertical == vertical)
        rows = (await self.db.execute(stmt.order_by(Service.vertical, Service.name))).scalars().all()
        return [
            ServiceInfo(
                code=r.code,
                name=r.name,
                vertical=r.vertical,
                duration_minutes=r.duration_minutes,
                description=r.description,
                preparation=r.preparation,
                documents_required=tuple(r.documents_required or ()),
                report_turnaround=r.report_turnaround,
            )
            for r in rows
        ]

    async def _load_snapshots(
        self, service_code: Optional[str] = None, vertical: Optional[str] = None
    ) -> list[SlotSnapshot]:
        stmt = (
            select(AppointmentSlot, Service, Clinician)
            .join(Service, Service.id == AppointmentSlot.service_id)
            .outerjoin(Clinician, Clinician.id == AppointmentSlot.clinician_id)
            .where(AppointmentSlot.status == SlotStatus.OPEN.value)
        )
        if service_code:
            stmt = stmt.where(Service.code == service_code)
        if vertical:
            stmt = stmt.where(Service.vertical == vertical)

        rows = (await self.db.execute(stmt)).all()
        return [
            SlotSnapshot(
                slot_id=str(slot.id),
                service_code=service.code,
                service_name=service.name,
                vertical=service.vertical,
                starts_at=_as_utc(slot.starts_at),
                ends_at=_as_utc(slot.ends_at),
                capacity=slot.capacity,
                booked_count=slot.booked_count,
                status=slot.status,
                clinician_name=clinician.name if clinician else None,
                location=slot.location,
            )
            for slot, service, clinician in rows
        ]

    async def find_slots(
        self,
        *,
        service_code: Optional[str] = None,
        vertical: Optional[str] = None,
        earliest: Optional[datetime] = None,
        latest: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[SlotSnapshot]:
        snapshots = await self._load_snapshots(service_code=service_code, vertical=vertical)
        return filter_slots(
            snapshots,
            service_code=service_code,
            vertical=vertical,
            earliest=earliest,
            latest=latest,
            limit=limit,
        )

    async def book(self, command: BookingCommand) -> BookingReceipt:
        slot = await self._get_slot(command.slot_id)
        service = await self.db.get(Service, slot.service_id)
        clinician = (
            await self.db.get(Clinician, slot.clinician_id) if slot.clinician_id else None
        )
        if service is None:
            raise SchedulingError("service_missing", "That slot is not linked to a service.")

        snapshot = SlotSnapshot(
            slot_id=str(slot.id),
            service_code=service.code,
            service_name=service.name,
            vertical=service.vertical,
            starts_at=_as_utc(slot.starts_at),
            ends_at=_as_utc(slot.ends_at),
            capacity=slot.capacity,
            booked_count=slot.booked_count,
            status=slot.status,
        )
        assert_bookable(snapshot)

        appointment = Appointment(
            reference_code=await self._unique_reference(),
            slot_id=slot.id,
            patient_id=uuid.UUID(command.patient_id) if command.patient_id else None,
            conversation_id=(
                uuid.UUID(command.conversation_id) if command.conversation_id else None
            ),
            patient_name=command.patient_name,
            phone=command.phone,
            email=command.email,
            status=AppointmentStatus.CONFIRMED.value,
            notes=command.notes,
        )
        slot.booked_count += 1
        if slot.booked_count >= slot.capacity:
            slot.status = SlotStatus.FULL.value

        self.db.add(appointment)
        await self.db.flush()

        return BookingReceipt(
            reference_code=appointment.reference_code,
            status=appointment.status,
            service_name=service.name,
            starts_at=_as_utc(slot.starts_at),
            patient_name=appointment.patient_name,
            phone=appointment.phone,
            clinician_name=clinician.name if clinician else None,
            location=slot.location,
            notes=appointment.notes,
        )

    async def lookup(self, reference_code: str) -> Optional[BookingReceipt]:
        appointment = await self._find_appointment(reference_code)
        if appointment is None:
            return None
        return await self._receipt_for(appointment)

    async def cancel(self, reference_code: str) -> BookingReceipt:
        appointment = await self._find_appointment(reference_code)
        if appointment is None:
            raise SchedulingError("not_found", f"No appointment found for {reference_code}.")
        if not can_cancel(appointment.status):
            raise SchedulingError(
                "not_cancellable",
                f"An appointment that is already {appointment.status} cannot be cancelled.",
            )

        if appointment.slot_id:
            slot = await self.db.get(AppointmentSlot, appointment.slot_id)
            if slot is not None:
                slot.booked_count = max(0, slot.booked_count - 1)
                if slot.status == SlotStatus.FULL.value and slot.booked_count < slot.capacity:
                    slot.status = SlotStatus.OPEN.value

        appointment.status = AppointmentStatus.CANCELLED.value
        await self.db.flush()
        return await self._receipt_for(appointment)

    async def reschedule(self, reference_code: str, new_slot_id: str) -> BookingReceipt:
        appointment = await self._find_appointment(reference_code)
        if appointment is None:
            raise SchedulingError("not_found", f"No appointment found for {reference_code}.")
        if not can_reschedule(appointment.status):
            raise SchedulingError(
                "not_reschedulable",
                f"An appointment that is already {appointment.status} cannot be moved.",
            )

        new_slot = await self._get_slot(new_slot_id)
        service = await self.db.get(Service, new_slot.service_id)
        if service is None:
            raise SchedulingError("service_missing", "That slot is not linked to a service.")

        assert_bookable(
            SlotSnapshot(
                slot_id=str(new_slot.id),
                service_code=service.code,
                service_name=service.name,
                vertical=service.vertical,
                starts_at=_as_utc(new_slot.starts_at),
                ends_at=_as_utc(new_slot.ends_at),
                capacity=new_slot.capacity,
                booked_count=new_slot.booked_count,
                status=new_slot.status,
            )
        )

        if appointment.slot_id:
            old_slot = await self.db.get(AppointmentSlot, appointment.slot_id)
            if old_slot is not None:
                old_slot.booked_count = max(0, old_slot.booked_count - 1)
                if old_slot.status == SlotStatus.FULL.value and old_slot.booked_count < old_slot.capacity:
                    old_slot.status = SlotStatus.OPEN.value

        new_slot.booked_count += 1
        if new_slot.booked_count >= new_slot.capacity:
            new_slot.status = SlotStatus.FULL.value

        appointment.slot_id = new_slot.id
        appointment.status = AppointmentStatus.RESCHEDULED.value
        await self.db.flush()
        return await self._receipt_for(appointment)

    async def _get_slot(self, slot_id: str) -> AppointmentSlot:
        try:
            parsed = uuid.UUID(slot_id)
        except (ValueError, AttributeError, TypeError) as exc:
            raise SchedulingError("bad_slot_id", f"'{slot_id}' is not a valid slot id.") from exc
        slot = await self.db.get(AppointmentSlot, parsed)
        if slot is None:
            raise SchedulingError("slot_not_found", "That slot no longer exists.")
        return slot

    async def _find_appointment(self, reference_code: str) -> Optional[Appointment]:
        stmt = select(Appointment).where(
            Appointment.reference_code == (reference_code or "").strip().upper()
        )
        return (await self.db.execute(stmt)).scalar_one_or_none()

    async def _unique_reference(self) -> str:
        for _ in range(10):
            code = generate_reference_code()
            existing = await self.db.execute(
                select(Appointment.id).where(Appointment.reference_code == code)
            )
            if existing.scalar_one_or_none() is None:
                return code
        raise SchedulingError("reference_exhausted", "Could not allocate a booking reference.")

    async def _receipt_for(self, appointment: Appointment) -> BookingReceipt:
        slot = (
            await self.db.get(AppointmentSlot, appointment.slot_id)
            if appointment.slot_id
            else None
        )
        service = await self.db.get(Service, slot.service_id) if slot else None
        clinician = (
            await self.db.get(Clinician, slot.clinician_id)
            if slot and slot.clinician_id
            else None
        )
        return BookingReceipt(
            reference_code=appointment.reference_code,
            status=appointment.status,
            service_name=service.name if service else "Appointment",
            starts_at=_as_utc(slot.starts_at) if slot else None,
            patient_name=appointment.patient_name,
            phone=appointment.phone,
            clinician_name=clinician.name if clinician else None,
            location=slot.location if slot else None,
            notes=appointment.notes,
        )


class HttpSchedulingProvider:
    """
    Forwards scheduling operations to an existing departmental REST API.

    Expected endpoints under ``SCHEDULING_API_BASE_URL``:
      GET  /services
      GET  /slots?service_code=&from=&to=&limit=
      POST /appointments
      GET  /appointments/{reference_code}
      POST /appointments/{reference_code}/cancel
      POST /appointments/{reference_code}/reschedule
    """

    name = "http"

    def __init__(self, base_url: str, api_key: str = "", timeout: float = 10.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=self._headers(), **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return None
            logger.error("Scheduling API %s %s failed: %s", method, path, exc)
            raise SchedulingError(
                "upstream_error",
                "The departmental scheduling system rejected that request.",
            ) from exc
        except httpx.HTTPError as exc:
            logger.error("Scheduling API %s %s unreachable: %s", method, path, exc)
            raise SchedulingError(
                "upstream_unavailable",
                "The departmental scheduling system is not reachable right now.",
            ) from exc

    async def list_services(self, vertical: Optional[str] = None) -> list[ServiceInfo]:
        params = {"vertical": vertical} if vertical else None
        payload = await self._request("GET", "/services", params=params) or []
        return [
            ServiceInfo(
                code=item["code"],
                name=item["name"],
                vertical=item.get("vertical", "department"),
                duration_minutes=int(item.get("duration_minutes", 30)),
                description=item.get("description", ""),
                preparation=item.get("preparation"),
                documents_required=tuple(item.get("documents_required") or ()),
                report_turnaround=item.get("report_turnaround"),
            )
            for item in payload
        ]

    async def find_slots(
        self,
        *,
        service_code: Optional[str] = None,
        vertical: Optional[str] = None,
        earliest: Optional[datetime] = None,
        latest: Optional[datetime] = None,
        limit: int = 10,
    ) -> list[SlotSnapshot]:
        params: dict[str, Any] = {"limit": limit}
        if service_code:
            params["service_code"] = service_code
        if vertical:
            params["vertical"] = vertical
        if earliest:
            params["from"] = earliest.isoformat()
        if latest:
            params["to"] = latest.isoformat()

        payload = await self._request("GET", "/slots", params=params) or []
        snapshots = [
            SlotSnapshot(
                slot_id=str(item["slot_id"]),
                service_code=item.get("service_code", service_code or ""),
                service_name=item.get("service_name", ""),
                vertical=item.get("vertical", "department"),
                starts_at=_parse_dt(item["starts_at"]),
                ends_at=_parse_dt(item.get("ends_at") or item["starts_at"]),
                capacity=int(item.get("capacity", 1)),
                booked_count=int(item.get("booked_count", 0)),
                status=item.get("status", SlotStatus.OPEN.value),
                clinician_name=item.get("clinician_name"),
                location=item.get("location"),
            )
            for item in payload
        ]
        # Re-apply our own rules; an upstream system may not enforce lead time.
        return filter_slots(snapshots, earliest=earliest, latest=latest, limit=limit)

    async def book(self, command: BookingCommand) -> BookingReceipt:
        payload = await self._request(
            "POST",
            "/appointments",
            json={
                "slot_id": command.slot_id,
                "patient_name": command.patient_name,
                "phone": command.phone,
                "email": command.email,
                "notes": command.notes,
            },
        )
        if not payload:
            raise SchedulingError("upstream_error", "The scheduling system did not confirm.")
        return _receipt_from_payload(payload, command.patient_name, command.phone)

    async def lookup(self, reference_code: str) -> Optional[BookingReceipt]:
        payload = await self._request("GET", f"/appointments/{reference_code}")
        if not payload:
            return None
        return _receipt_from_payload(payload)

    async def cancel(self, reference_code: str) -> BookingReceipt:
        payload = await self._request("POST", f"/appointments/{reference_code}/cancel")
        if not payload:
            raise SchedulingError("not_found", f"No appointment found for {reference_code}.")
        return _receipt_from_payload(payload)

    async def reschedule(self, reference_code: str, new_slot_id: str) -> BookingReceipt:
        payload = await self._request(
            "POST",
            f"/appointments/{reference_code}/reschedule",
            json={"slot_id": new_slot_id},
        )
        if not payload:
            raise SchedulingError("not_found", f"No appointment found for {reference_code}.")
        return _receipt_from_payload(payload)


def get_scheduling_provider(db: AsyncSession) -> SchedulingProvider:
    """Pick a provider from settings, falling back to local if http is misconfigured."""
    settings = get_settings()
    if settings.scheduling_provider == "http":
        if settings.scheduling_api_base_url:
            return HttpSchedulingProvider(
                base_url=settings.scheduling_api_base_url,
                api_key=settings.scheduling_api_key,
                timeout=settings.scheduling_api_timeout_seconds,
            )
        logger.warning(
            "SCHEDULING_PROVIDER=http but SCHEDULING_API_BASE_URL is empty — using local provider"
        )
    return LocalSchedulingProvider(db)


def _as_utc(moment: datetime) -> datetime:
    """Postgres may hand back naive datetimes; scheduling maths needs tz-aware."""
    if moment.tzinfo is None:
        return moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def _parse_dt(value: str) -> datetime:
    return _as_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))


def _receipt_from_payload(
    payload: dict[str, Any],
    fallback_name: str = "",
    fallback_phone: str = "",
) -> BookingReceipt:
    starts_at = payload.get("starts_at")
    return BookingReceipt(
        reference_code=payload.get("reference_code", ""),
        status=payload.get("status", AppointmentStatus.CONFIRMED.value),
        service_name=payload.get("service_name", "Appointment"),
        starts_at=_parse_dt(starts_at) if starts_at else None,
        patient_name=payload.get("patient_name", fallback_name),
        phone=payload.get("phone", fallback_phone),
        clinician_name=payload.get("clinician_name"),
        location=payload.get("location"),
        notes=payload.get("notes"),
    )
