"""
Deterministic rules engine for concern → tests recommendations.

HARD CONSTRAINT: This module must NEVER call an LLM. All mappings come from
ConcernConfig (+ optional conditional_rules) and TestCatalog in the database.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class ConcernConfigSnapshot:
    """In-memory snapshot of a ConcernConfig row (for pure functions / tests)."""

    concern_type: str
    age_band: Optional[str]
    recommended_tests: list[str]
    what_it_helps: str
    outcome_options: Optional[list[str]] = None
    conditional_rules: Optional[list[dict[str, Any]]] = None
    common_signs: Optional[list[dict[str, Any]]] = None


@dataclass(frozen=True)
class CatalogEntry:
    code: str
    name: str
    category: str
    description: str


@dataclass(frozen=True)
class RecommendationResult:
    test_codes: list[str]
    what_it_helps: str
    outcome_options: Optional[list[str]]
    reasons: dict[str, str]  # code → why included


def _answer_matches(answer: str, rule: dict[str, Any]) -> bool:
    answer_l = answer.lower().strip()
    if "answer_equals" in rule:
        return answer_l == str(rule["answer_equals"]).lower().strip()
    if "answer_contains" in rule:
        return str(rule["answer_contains"]).lower() in answer_l
    if "answer_in" in rule:
        options = [str(x).lower().strip() for x in rule["answer_in"]]
        return answer_l in options
    # Default: any non-empty / affirmative-ish answer triggers
    if rule.get("answer_truthy"):
        return answer_l not in {"", "no", "n", "false", "none", "0"}
    return False


def apply_conditional_rules(
    base_tests: Sequence[str],
    conditional_rules: Optional[Sequence[dict[str, Any]]],
    symptom_answers: dict[str, str],
) -> tuple[list[str], dict[str, str]]:
    """
    Expand the base test list using config-driven conditional rules.

    Rule shape (JSONB on ConcernConfig.conditional_rules):
      {
        "when": {"question_key": "sudden", "answer_contains": "sudden"},
        "add_tests": ["ABR"],
        "reason": "Sudden onset warrants ABR"
      }
    """
    codes = list(dict.fromkeys(base_tests))  # preserve order, unique
    reasons: dict[str, str] = {c: "Configured for this concern pathway" for c in codes}

    if not conditional_rules:
        return codes, reasons

    for rule in conditional_rules:
        when = rule.get("when") or {}
        qkey = when.get("question_key")
        if not qkey:
            continue
        answer = symptom_answers.get(qkey)
        if answer is None:
            continue
        if not _answer_matches(answer, when):
            continue
        add_tests = rule.get("add_tests") or []
        reason = rule.get("reason") or "Added by symptom-based rule"
        for code in add_tests:
            if code not in codes:
                codes.append(code)
            reasons[code] = reason

    return codes, reasons


def recommend_tests(
    config: ConcernConfigSnapshot,
    symptom_answers: Optional[dict[str, str]] = None,
) -> RecommendationResult:
    """
    Pure function: given a ConcernConfig snapshot and optional symptom answers,
    return the ordered recommended test codes and reasons.
    """
    answers = symptom_answers or {}
    codes, reasons = apply_conditional_rules(
        config.recommended_tests,
        config.conditional_rules,
        answers,
    )
    return RecommendationResult(
        test_codes=codes,
        what_it_helps=config.what_it_helps,
        outcome_options=list(config.outcome_options) if config.outcome_options else None,
        reasons=reasons,
    )


def enrich_with_catalog(
    result: RecommendationResult,
    catalog_by_code: dict[str, CatalogEntry],
) -> list[dict[str, str]]:
    """Attach catalog metadata to recommended codes. Unknown codes are skipped."""
    enriched: list[dict[str, str]] = []
    for code in result.test_codes:
        info = catalog_by_code.get(code)
        if not info:
            continue
        enriched.append(
            {
                "code": info.code,
                "name": info.name,
                "category": info.category,
                "description": info.description,
                "reason": result.reasons.get(code, "Configured for this concern pathway"),
            }
        )
    return enriched


GENERAL_RECOMMENDATIONS_ADULT: list[str] = [
    "Avoid loud noise exposure",
    "Protect ears in noisy places",
    "Get enough rest and sleep",
    "Manage stress and anxiety",
    "Stay hydrated and healthy",
    "Regular hearing check-ups",
    "Consult an audiologist for a professional assessment",
]

GENERAL_RECOMMENDATIONS_CHILD: list[str] = [
    "Hearing Aid evaluation (if indicated)",
    "ENT Referral when middle-ear disease is suspected",
    "Cochlear Implant Evaluation for severe–profound loss",
    "Auditory Training",
    "Speech Therapy",
    "Parent Counselling",
    "Regular Follow-up",
    "Consult a paediatric audiologist",
]


def general_recommendations_for(concern_type: str, age_band: Optional[str] = None) -> list[str]:
    if concern_type == "child_concerns" or age_band:
        return list(GENERAL_RECOMMENDATIONS_CHILD)
    return list(GENERAL_RECOMMENDATIONS_ADULT)
