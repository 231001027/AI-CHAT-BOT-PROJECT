"""
Seed content for the clinical flow: categories, conditions, branching questions
and clinical rules.

IMPORTANT — this is starting content, NOT clinically signed off. It is modelled on
standard audiology practice so the flow is usable on day one, and is expected to
be reviewed and replaced by the department through the admin screens. Everything
here is editable at runtime; nothing is hardcoded in the engine.

Question ``key`` values are the field names rules match on, so renaming a key
means updating the rules that reference it.
"""

from __future__ import annotations

from typing import Any

from app.services.clinical_seed_adult import (
    ADULT_CATEGORIES,
    ADULT_CONDITIONS,
    ADULT_QUESTIONS,
    ADULT_RULES,
)
from app.services.clinical_seed_child import (
    CHILD_CATEGORIES,
    CHILD_CONDITIONS,
    CHILD_QUESTIONS,
    CHILD_RULES,
)

CATEGORIES: list[dict[str, Any]] = ADULT_CATEGORIES + CHILD_CATEGORIES
CONDITIONS: list[dict[str, Any]] = ADULT_CONDITIONS + CHILD_CONDITIONS
QUESTIONS: list[dict[str, Any]] = ADULT_QUESTIONS + CHILD_QUESTIONS
RULES: list[dict[str, Any]] = ADULT_RULES + CHILD_RULES
