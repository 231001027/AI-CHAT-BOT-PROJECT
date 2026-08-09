"""Unit tests for deterministic scheduling rules."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import AppointmentStatus, SlotStatus, Vertical
from app.services.scheduling import (
    MIN_LEAD_TIME,
    SchedulingError,
    SlotSnapshot,
    assert_bookable,
    can_cancel,
    can_reschedule,
    describe_slot,
    filter_slots,
    generate_reference_code,
    is_bookable,
    is_within_working_hours,
    next_available,
    summarise_availability,
)

NOW = datetime(2026, 8, 3, 9, 0, tzinfo=timezone.utc)  # a Monday


def _slot(**overrides) -> SlotSnapshot:
    defaults = {
        "slot_id": "slot-1",
        "service_code": "AUD_ASSESSMENT",
        "service_name": "Comprehensive Audiological Assessment",
        "vertical": Vertical.AUDIOLOGY.value,
        "starts_at": NOW + timedelta(days=1),
        "ends_at": NOW + timedelta(days=1, hours=1),
        "capacity": 1,
        "booked_count": 0,
        "status": SlotStatus.OPEN.value,
        "clinician_name": "Dr. A. Raghavan",
        "location": "Audiology Block",
    }
    defaults.update(overrides)
    return SlotSnapshot(**defaults)


class TestSeatsLeft:
    def test_open_slot_has_seats(self):
        assert _slot(capacity=3, booked_count=1).seats_left == 2

    def test_full_slot_has_no_seats(self):
        assert _slot(capacity=2, booked_count=2).seats_left == 0

    def test_overbooked_never_reports_negative(self):
        assert _slot(capacity=1, booked_count=5).seats_left == 0


class TestIsBookable:
    def test_future_open_slot_is_bookable(self):
        assert is_bookable(_slot(), now=NOW)

    def test_full_slot_is_not_bookable(self):
        assert not is_bookable(_slot(capacity=1, booked_count=1), now=NOW)

    def test_blocked_slot_is_not_bookable(self):
        assert not is_bookable(_slot(status=SlotStatus.BLOCKED.value), now=NOW)

    def test_past_slot_is_not_bookable(self):
        assert not is_bookable(_slot(starts_at=NOW - timedelta(hours=1)), now=NOW)

    def test_slot_inside_lead_time_is_not_bookable(self):
        too_soon = _slot(starts_at=NOW + MIN_LEAD_TIME - timedelta(minutes=1))
        assert not is_bookable(too_soon, now=NOW)

    def test_slot_exactly_at_lead_time_is_bookable(self):
        assert is_bookable(_slot(starts_at=NOW + MIN_LEAD_TIME), now=NOW)


class TestFilterSlots:
    def test_returns_soonest_first(self):
        slots = [
            _slot(slot_id="late", starts_at=NOW + timedelta(days=5)),
            _slot(slot_id="early", starts_at=NOW + timedelta(days=1)),
        ]
        assert [s.slot_id for s in filter_slots(slots, now=NOW)] == ["early", "late"]

    def test_filters_by_service_code(self):
        slots = [
            _slot(slot_id="aud", service_code="AUD_ASSESSMENT"),
            _slot(slot_id="slp", service_code="SLP_THERAPY"),
        ]
        found = filter_slots(slots, service_code="SLP_THERAPY", now=NOW)
        assert [s.slot_id for s in found] == ["slp"]

    def test_filters_by_vertical(self):
        slots = [
            _slot(slot_id="aud", vertical=Vertical.AUDIOLOGY.value),
            _slot(slot_id="slp", vertical=Vertical.SLP.value),
        ]
        found = filter_slots(slots, vertical=Vertical.SLP.value, now=NOW)
        assert [s.slot_id for s in found] == ["slp"]

    def test_excludes_unbookable_slots(self):
        slots = [
            _slot(slot_id="ok"),
            _slot(slot_id="full", capacity=1, booked_count=1),
            _slot(slot_id="past", starts_at=NOW - timedelta(days=1)),
        ]
        assert [s.slot_id for s in filter_slots(slots, now=NOW)] == ["ok"]

    def test_respects_search_horizon(self):
        far = _slot(slot_id="far", starts_at=NOW + timedelta(days=60))
        assert filter_slots([far], now=NOW) == []

    def test_respects_explicit_window(self):
        slots = [
            _slot(slot_id="d1", starts_at=NOW + timedelta(days=1)),
            _slot(slot_id="d10", starts_at=NOW + timedelta(days=10)),
        ]
        found = filter_slots(slots, earliest=NOW + timedelta(days=5), now=NOW)
        assert [s.slot_id for s in found] == ["d10"]

    def test_respects_limit(self):
        slots = [_slot(slot_id=f"s{i}", starts_at=NOW + timedelta(days=i)) for i in range(1, 8)]
        assert len(filter_slots(slots, now=NOW, limit=3)) == 3

    def test_ties_broken_deterministically_by_id(self):
        same_time = NOW + timedelta(days=1)
        slots = [_slot(slot_id="b", starts_at=same_time), _slot(slot_id="a", starts_at=same_time)]
        assert [s.slot_id for s in filter_slots(slots, now=NOW)] == ["a", "b"]

    def test_empty_input_returns_empty(self):
        assert filter_slots([], now=NOW) == []


class TestNextAvailable:
    def test_picks_the_soonest_bookable_slot(self):
        slots = [
            _slot(slot_id="later", starts_at=NOW + timedelta(days=3)),
            _slot(slot_id="sooner", starts_at=NOW + timedelta(days=2)),
        ]
        found = next_available(slots, now=NOW)
        assert found is not None and found.slot_id == "sooner"

    def test_returns_none_when_nothing_bookable(self):
        assert next_available([_slot(status=SlotStatus.BLOCKED.value)], now=NOW) is None


class TestAssertBookable:
    def test_passes_for_valid_slot(self):
        assert_bookable(_slot(), now=NOW)

    def test_blocked_raises_with_code(self):
        with pytest.raises(SchedulingError) as exc:
            assert_bookable(_slot(status=SlotStatus.BLOCKED.value), now=NOW)
        assert exc.value.code == "slot_blocked"

    def test_full_raises_with_code(self):
        with pytest.raises(SchedulingError) as exc:
            assert_bookable(_slot(capacity=1, booked_count=1), now=NOW)
        assert exc.value.code == "slot_full"

    def test_past_raises_with_code(self):
        with pytest.raises(SchedulingError) as exc:
            assert_bookable(_slot(starts_at=NOW - timedelta(hours=2)), now=NOW)
        assert exc.value.code == "slot_past"

    def test_too_soon_raises_with_code(self):
        with pytest.raises(SchedulingError) as exc:
            assert_bookable(_slot(starts_at=NOW + timedelta(minutes=30)), now=NOW)
        assert exc.value.code == "slot_too_soon"


class TestStatusTransitions:
    @pytest.mark.parametrize(
        "status",
        [
            AppointmentStatus.REQUESTED.value,
            AppointmentStatus.CONFIRMED.value,
            AppointmentStatus.RESCHEDULED.value,
        ],
    )
    def test_active_appointments_can_be_changed(self, status):
        assert can_cancel(status)
        assert can_reschedule(status)

    @pytest.mark.parametrize(
        "status",
        [
            AppointmentStatus.CANCELLED.value,
            AppointmentStatus.COMPLETED.value,
            AppointmentStatus.NO_SHOW.value,
        ],
    )
    def test_closed_appointments_cannot_be_changed(self, status):
        assert not can_cancel(status)
        assert not can_reschedule(status)


class TestReferenceCode:
    def test_has_expected_shape(self):
        code = generate_reference_code(random.Random(42))
        assert code.startswith("NIEPMD-")
        assert len(code) == len("NIEPMD-") + 6

    def test_is_seeded_reproducibly(self):
        assert generate_reference_code(random.Random(7)) == generate_reference_code(random.Random(7))

    def test_differs_across_seeds(self):
        assert generate_reference_code(random.Random(1)) != generate_reference_code(random.Random(2))


class TestWorkingHours:
    def test_weekday_morning_is_working_time(self):
        assert is_within_working_hours(NOW)

    def test_weekend_is_not_working_time(self):
        saturday = datetime(2026, 8, 8, 10, 0, tzinfo=timezone.utc)
        assert not is_within_working_hours(saturday)

    def test_evening_is_not_working_time(self):
        assert not is_within_working_hours(NOW.replace(hour=20))


class TestDescriptions:
    def test_describe_includes_service_clinician_and_location(self):
        text = describe_slot(_slot())
        assert "Comprehensive Audiological Assessment" in text
        assert "Dr. A. Raghavan" in text
        assert "Audiology Block" in text

    def test_describe_omits_missing_optional_fields(self):
        text = describe_slot(_slot(clinician_name=None, location=None))
        assert "with" not in text
        assert "at " not in text

    def test_summarise_numbers_the_options(self):
        slots = [_slot(slot_id="a"), _slot(slot_id="b", starts_at=NOW + timedelta(days=2))]
        summary = summarise_availability(slots)
        assert summary.startswith("1. ")
        assert "2. " in summary

    def test_summarise_respects_limit(self):
        slots = [_slot(slot_id=f"s{i}", starts_at=NOW + timedelta(days=i)) for i in range(1, 8)]
        assert len(summarise_availability(slots, limit=3).splitlines()) == 3

    def test_summarise_handles_no_slots(self):
        assert "No open slots" in summarise_availability([])
