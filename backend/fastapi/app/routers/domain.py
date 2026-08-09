"""Static domain data endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.data.domain import (
    ADULT_SECTIONS,
    CHILD_CATEGORIES,
    HEARING_PROBLEMS,
    SPECIAL_TESTS,
)
from app.schemas import AdultSection, ChildCategory, HearingProblem, SpecialTest

router = APIRouter(prefix="/api", tags=["Data"])


@router.get("/hearing-problems", response_model=list[HearingProblem])
def get_hearing_problems():
    """Return hearing problem categories shown on the Assessment page."""
    return HEARING_PROBLEMS


@router.get("/adult-sections", response_model=list[AdultSection])
def get_adult_sections():
    """Return adult care sections shown on the Adult Care page."""
    return ADULT_SECTIONS


@router.get("/special-tests", response_model=list[SpecialTest])
def get_special_tests():
    """Return the list of special audiological tests."""
    return SPECIAL_TESTS


@router.get("/child-categories", response_model=list[ChildCategory])
def get_child_categories():
    """Return paediatric hearing assessment categories."""
    return CHILD_CATEGORIES
