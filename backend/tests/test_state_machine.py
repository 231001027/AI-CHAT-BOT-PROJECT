"""State machine unit tests."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.models.enums import AgeBand, ConcernType, SessionStep, UserType
from app.services import state_machine as sm


def test_happy_path_transitions():
    assert sm.can_transition(SessionStep.WELCOME, SessionStep.USER_TYPE)
    assert sm.can_transition(SessionStep.USER_TYPE, SessionStep.PROFILE)
    assert sm.can_transition(SessionStep.PROFILE, SessionStep.CONCERN_SELECT)
    assert sm.can_transition(SessionStep.CONCERN_SELECT, SessionStep.SYMPTOMS)
    assert sm.can_transition(SessionStep.SYMPTOMS, SessionStep.RECOMMENDATIONS)


def test_invalid_transition_raises():
    with pytest.raises(HTTPException) as exc:
        sm.transition(SessionStep.WELCOME, SessionStep.BOOKING)
    assert exc.value.status_code == 409


def test_assert_step():
    sm.assert_step(SessionStep.PROFILE, {SessionStep.PROFILE}, "save_profile")
    with pytest.raises(HTTPException):
        sm.assert_step(SessionStep.WELCOME, {SessionStep.PROFILE}, "save_profile")


def test_route_hint():
    assert sm.route_hint_for_profile(UserType.MY_CHILD, 30) == "child"
    assert sm.route_hint_for_profile(UserType.MYSELF, 10) == "child"
    assert sm.route_hint_for_profile(UserType.MYSELF, 12) == "child"
    assert sm.route_hint_for_profile(UserType.MYSELF, 13) == "adult"
    assert sm.route_hint_for_profile(UserType.MYSELF, 40) == "adult"


def test_age_band_mapping():
    assert sm.age_band_for_age(0.2) == AgeBand.NEWBORN
    assert sm.age_band_for_age(1.0) == AgeBand.INFANT_TODDLER
    assert sm.age_band_for_age(3.0) == AgeBand.PRESCHOOL
    assert sm.age_band_for_age(8.0) == AgeBand.SCHOOL_AGE
    assert sm.age_band_for_age(12.0) == AgeBand.SCHOOL_AGE
    assert sm.age_band_for_age(13.0) is None


def test_source_page():
    assert sm.source_page_for_concern(ConcernType.TINNITUS, None) == "page2_adult"
    assert (
        sm.source_page_for_concern(ConcernType.CHILD_CONCERNS, AgeBand.NEWBORN)
        == "page3_child"
    )
