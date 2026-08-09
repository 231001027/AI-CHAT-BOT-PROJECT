"""
Deterministic appointment logic.

Pure functions over slot snapshots so booking rules are unit-testable without a
database and identical whether a slot came from our own tables or from an
external departmental scheduling system.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from app.models.enums import AppointmentStatus, SlotStatus

# Department working pattern, used when suggesting alternatives.
WORKING_DAYS: frozenset[int] = frozenset({0, 1, 2, 3, 4})  # Mon–Fri
WORKING_HOURS: tuple[int, int] = (9, 17)

# A patient cannot book a slot starting sooner than this.
MIN_LEAD_TIME = timedelta(hours=2)

# How far ahead slot searches look by default.
DEFAULT_SEARCH_WINDOW_DAYS = 21

REFERENCE_PREFIX = "NIEPMD"
REFERENCE_ALPHABET = string.ascii_uppercase + string.digits


@dataclass(frozen=True)
class SlotSnapshot:
    """DB-free view of a bookable slot."""

    slot_id: str
    service_code: str
    service_name: str
    vertical: str
    starts_at: datetime
    ends_at: datetime
    capacity: int
    booked_count: int
    status: str = SlotStatus.OPEN.value
    clinician_name: Optional[str] = None
    location: Optional[str] = None

    @property
    def seats_left(self) -> int:
        return max(0, self.capacity - self.booked_count)


class SchedulingError(Exception):
    """Raised when a booking request violates a scheduling rule."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def generate_reference_code(rng: Optional[random.Random] = None) -> str:
    """Short human-readable code patients can quote on the phone."""
    source = rng or random
    body = "".join(source.choice(REFERENCE_ALPHABET) for _ in range(6))
    return f"{REFERENCE_PREFIX}-{body}"


def is_within_working_hours(moment: datetime) -> bool:
    start, end = WORKING_HOURS
    return moment.weekday() in WORKING_DAYS and start <= moment.hour < end


def is_bookable(slot: SlotSnapshot, *, now: Optional[datetime] = None) -> bool:
    """A slot is bookable if it is open, has a seat, and is far enough ahead."""
    reference = now or datetime.now(timezone.utc)
    if slot.status != SlotStatus.OPEN.value:
        return False
    if slot.seats_left <= 0:
        return False
    return slot.starts_at - reference >= MIN_LEAD_TIME


def filter_slots(
    slots: Sequence[SlotSnapshot],
    *,
    service_code: Optional[str] = None,
    vertical: Optional[str] = None,
    earliest: Optional[datetime] = None,
    latest: Optional[datetime] = None,
    now: Optional[datetime] = None,
    limit: int = 10,
) -> list[SlotSnapshot]:
    """Bookable slots matching the filters, soonest first."""
    reference = now or datetime.now(timezone.utc)
    horizon = latest or reference + timedelta(days=DEFAULT_SEARCH_WINDOW_DAYS)
    floor = earliest or reference

    matches = [
        s
        for s in slots
        if is_bookable(s, now=reference)
        and (service_code is None or s.service_code == service_code)
        and (vertical is None or s.vertical == vertical)
        and s.starts_at >= floor
        and s.starts_at <= horizon
    ]
    matches.sort(key=lambda s: (s.starts_at, s.slot_id))
    return matches[:limit]


def next_available(
    slots: Sequence[SlotSnapshot],
    *,
    service_code: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Optional[SlotSnapshot]:
    found = filter_slots(slots, service_code=service_code, now=now, limit=1)
    return found[0] if found else None


def assert_bookable(slot: SlotSnapshot, *, now: Optional[datetime] = None) -> None:
    """Raise a typed SchedulingError explaining exactly why a booking failed."""
    reference = now or datetime.now(timezone.utc)
    if slot.status == SlotStatus.BLOCKED.value:
        raise SchedulingError("slot_blocked", "That slot has been blocked by the department.")
    if slot.seats_left <= 0:
        raise SchedulingError("slot_full", "That slot is already fully booked.")
    if slot.starts_at <= reference:
        raise SchedulingError("slot_past", "That slot is in the past.")
    if slot.starts_at - reference < MIN_LEAD_TIME:
        raise SchedulingError(
            "slot_too_soon",
            "Appointments need to be booked at least 2 hours in advance.",
        )


def can_cancel(status: str) -> bool:
    return status in {
        AppointmentStatus.REQUESTED.value,
        AppointmentStatus.CONFIRMED.value,
        AppointmentStatus.RESCHEDULED.value,
    }


def can_reschedule(status: str) -> bool:
    return can_cancel(status)


def describe_slot(slot: SlotSnapshot) -> str:
    """Patient-facing one-liner, e.g. 'Mon 04 Aug, 10:30 AM — Pure Tone Audiometry'."""
    when = slot.starts_at.strftime("%a %d %b, %I:%M %p").replace(" 0", " ")
    parts = [f"{when} — {slot.service_name}"]
    if slot.clinician_name:
        parts.append(f"with {slot.clinician_name}")
    if slot.location:
        parts.append(f"at {slot.location}")
    return " ".join(parts)


def summarise_availability(slots: Sequence[SlotSnapshot], limit: int = 5) -> str:
    """Numbered availability list the scheduling assistant reads back verbatim."""
    if not slots:
        return "No open slots were found in the requested window."
    lines = [f"{i}. {describe_slot(s)}" for i, s in enumerate(slots[:limit], start=1)]
    return "\n".join(lines)
