"""
ChatSession step state machine.

Validates that incoming requests match the expected current step and
computes transitions for Page 1 → Page 2 (adult) / Page 3 (child).
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status

from app.models.enums import (
    AgeBand,
    ConcernType,
    SessionStep,
    STEP_TRANSITIONS,
    UserType,
)


class InvalidStepError(Exception):
    def __init__(self, current: SessionStep, expected: set[SessionStep], action: str):
        self.current = current
        self.expected = expected
        self.action = action
        super().__init__(
            f"Cannot perform '{action}' at step '{current}'. Expected one of: {sorted(s.value for s in expected)}"
        )


def parse_step(value: str) -> SessionStep:
    try:
        return SessionStep(value)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown session step: {value}",
        ) from exc


def assert_step(current: SessionStep, allowed: set[SessionStep], action: str) -> None:
    if current not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_step",
                "action": action,
                "current_step": current.value,
                "allowed_steps": [s.value for s in sorted(allowed, key=lambda x: x.value)],
            },
        )


def can_transition(current: SessionStep, nxt: SessionStep) -> bool:
    return nxt in STEP_TRANSITIONS.get(current, frozenset())


def transition(current: SessionStep, nxt: SessionStep) -> SessionStep:
    if not can_transition(current, nxt):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "invalid_transition",
                "from": current.value,
                "to": nxt.value,
                "allowed": [s.value for s in STEP_TRANSITIONS.get(current, frozenset())],
            },
        )
    return nxt


def route_hint_for_profile(user_type: UserType, age: int) -> str:
    """Decide adult vs child pathway after profile is saved."""
    if user_type == UserType.MY_CHILD:
        return "child"
    # Clinic rule: under 13 = child, 13 and above = adult.
    if age < 13:
        return "child"
    return "adult"


def age_band_for_age(age_years: float) -> Optional[AgeBand]:
    """
    Map chronological age to a child age band.
    age_years may be fractional (e.g. 0.3 for ~3.5 months).
    Returns None for ages 13+ (adult pathway).
    """
    if age_years < 0:
        return None
    if age_years >= 13:
        return None
    months = age_years * 12
    if months <= 6:
        return AgeBand.NEWBORN
    if age_years < 2.5:
        return AgeBand.INFANT_TODDLER
    if age_years < 5:
        return AgeBand.PRESCHOOL
    return AgeBand.SCHOOL_AGE


def source_page_for_concern(concern_type: ConcernType, age_band: Optional[AgeBand]) -> str:
    if concern_type == ConcernType.CHILD_CONCERNS or age_band is not None:
        return "page3_child"
    return "page2_adult"


def next_after_user_type() -> SessionStep:
    return SessionStep.PROFILE


def next_after_profile() -> SessionStep:
    return SessionStep.CONCERN_SELECT


def next_after_concern_selected() -> SessionStep:
    return SessionStep.SYMPTOMS


def next_after_symptoms_complete() -> SessionStep:
    return SessionStep.RECOMMENDATIONS
