"""
Deterministic clinical rule engine.

HARD CONSTRAINT: no LLM, no network, no database. Pure functions over a fact
dictionary and admin-authored rule definitions, so a clinician can reason about
exactly which tests a given set of answers produces, and so the whole engine is
unit-testable.

A rule definition is a boolean tree:

    {"all": [{"field": "sudden", "op": "eq", "value": "yes"},
             {"any": [{"field": "age", "op": ">=", "value": 60},
                      {"field": "noise_exposure", "op": "truthy"}]}]}

Leaves are ``{"field", "op", "value"}``. Branches are ``all`` / ``any`` / ``not``.
An empty definition matches nothing, which is deliberate — a misconfigured rule
should stay silent rather than fire for every patient.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

logger = logging.getLogger("nipmed.clinical_rules")

# Operator aliases so admins can write either symbols or words.
OPERATORS: dict[str, str] = {
    "eq": "eq",
    "==": "eq",
    "=": "eq",
    "ne": "ne",
    "!=": "ne",
    "gt": "gt",
    ">": "gt",
    "gte": "gte",
    ">=": "gte",
    "lt": "lt",
    "<": "lt",
    "lte": "lte",
    "<=": "lte",
    "in": "in",
    "not_in": "not_in",
    "contains": "contains",
    "exists": "exists",
    "truthy": "truthy",
    "falsy": "falsy",
}

# Answer values treated as an affirmative for `truthy`.
TRUTHY_VALUES: frozenset[str] = frozenset(
    {"yes", "y", "true", "1", "present", "sudden", "both", "left", "right", "often", "always"}
)

FALSY_VALUES: frozenset[str] = frozenset(
    {"no", "n", "false", "0", "absent", "none", "never", "not_sure", "unsure", "dont_know"}
)


@dataclass(frozen=True)
class TestRecommendation:
    # Stops pytest trying to collect this as a test class on import.
    __test__ = False

    test_code: str
    test_name: str
    reason_text: str
    rule_name: str
    priority: int = 0
    display_order: int = 0


@dataclass(frozen=True)
class RuleSnapshot:
    """DB-free view of a ClinicalRule plus the tests it recommends."""

    rule_id: str
    name: str
    rule_definition: dict[str, Any]
    tests: tuple[TestRecommendation, ...]
    priority: int = 0
    is_baseline: bool = False
    condition_id: Optional[str] = None


@dataclass(frozen=True)
class RecommendationOutcome:
    tests: tuple[TestRecommendation, ...] = ()
    matched_rule_ids: tuple[str, ...] = ()
    general_recommendations: tuple[str, ...] = ()
    # Rules skipped because their definition was malformed, surfaced to admins
    invalid_rule_ids: tuple[str, ...] = field(default=())


class RuleEvaluationError(ValueError):
    """Raised for a structurally invalid rule definition."""


# ---------------------------------------------------------------------------
# Predicate evaluation
# ---------------------------------------------------------------------------


def _coerce_pair(left: Any, right: Any) -> tuple[Any, Any]:
    """
    Make two values comparable.

    Answers arrive as strings, so "12" from a form and 12 from a rule must
    compare numerically. Falls back to case-insensitive strings.
    """
    if isinstance(left, bool) or isinstance(right, bool):
        return bool(left), bool(right)

    for caster in (int, float):
        try:
            return caster(left), caster(right)
        except (TypeError, ValueError):
            continue

    return str(left).strip().lower(), str(right).strip().lower()


def _numeric(value: Any) -> Optional[float]:
    """Return ``value`` as a float, or None if it is not a number."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _equals(left: Any, right: Any) -> bool:
    """Type-tolerant equality used by eq, ne, in and not_in."""
    coerced_left, coerced_right = _coerce_pair(left, right)
    return coerced_left == coerced_right


def _is_truthy(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    text = str(value).strip().lower()
    if not text:
        return False
    if text in FALSY_VALUES:
        return False
    if text in TRUTHY_VALUES:
        return True
    # Any other non-empty answer counts as present.
    return True


def evaluate_leaf(node: dict[str, Any], facts: dict[str, Any]) -> bool:
    """Evaluate a single ``{"field", "op", "value"}`` predicate."""
    field_name = node.get("field")
    if not field_name:
        raise RuleEvaluationError("Leaf predicate is missing 'field'")

    raw_op = str(node.get("op", "eq"))
    op = OPERATORS.get(raw_op)
    if op is None:
        raise RuleEvaluationError(f"Unknown operator: {raw_op}")

    actual = facts.get(field_name)
    expected = node.get("value")

    if op == "exists":
        return field_name in facts and facts[field_name] is not None
    if op == "truthy":
        return _is_truthy(actual)
    if op == "falsy":
        return not _is_truthy(actual)

    # Every remaining operator needs an answer to compare against.
    if actual is None:
        return False

    if op in {"in", "not_in"}:
        if not isinstance(expected, (list, tuple, set)):
            raise RuleEvaluationError(f"'{op}' requires a list value")
        found = any(_equals(actual, item) for item in expected)
        return found if op == "in" else not found
    if op == "contains":
        return str(expected).strip().lower() in str(actual).strip().lower()

    if op == "eq":
        return _equals(actual, expected)
    if op == "ne":
        return not _equals(actual, expected)

    # Ordered comparisons. When the rule's threshold is numeric the answer must
    # be numeric too, otherwise "male" > 5 would silently succeed as a string
    # comparison and the rule would fire for the wrong patients.
    expected_number = _numeric(expected)
    if expected_number is not None:
        actual_number = _numeric(actual)
        if actual_number is None:
            return False
        left, right = actual_number, expected_number
    else:
        left, right = str(actual).strip().lower(), str(expected).strip().lower()

    try:
        if op == "gt":
            return left > right
        if op == "gte":
            return left >= right
        if op == "lt":
            return left < right
        if op == "lte":
            return left <= right
    except TypeError:
        return False

    raise RuleEvaluationError(f"Unhandled operator: {op}")


def evaluate_predicate(node: Any, facts: dict[str, Any]) -> bool:
    """Recursively evaluate a rule definition node."""
    if not isinstance(node, dict) or not node:
        # An empty or non-dict node never matches.
        return False

    if "all" in node:
        children = node["all"]
        if not isinstance(children, list):
            raise RuleEvaluationError("'all' must be a list")
        return all(evaluate_predicate(child, facts) for child in children) if children else False

    if "any" in node:
        children = node["any"]
        if not isinstance(children, list):
            raise RuleEvaluationError("'any' must be a list")
        return any(evaluate_predicate(child, facts) for child in children)

    if "not" in node:
        return not evaluate_predicate(node["not"], facts)

    return evaluate_leaf(node, facts)


def rule_matches(rule: RuleSnapshot, facts: dict[str, Any]) -> bool:
    """
    Whether a rule fires for these facts.

    Baseline rules always fire — they carry the tests every patient with this
    condition receives, independent of their answers.
    """
    if rule.is_baseline:
        return True
    return evaluate_predicate(rule.rule_definition, facts)


# ---------------------------------------------------------------------------
# Recommendation assembly
# ---------------------------------------------------------------------------


def recommend_tests(
    rules: Sequence[RuleSnapshot],
    facts: dict[str, Any],
    *,
    general_recommendations: Optional[Iterable[str]] = None,
) -> RecommendationOutcome:
    """
    Run every rule and assemble a deduplicated, ordered test list.

    Ordering is rule priority descending, then the rule's own display order, so
    the clinically most important tests appear first. The first rule to introduce
    a test owns its reason text; later duplicates are dropped rather than
    appended, to avoid contradictory reasons for one test.
    """
    matched_ids: list[str] = []
    invalid_ids: list[str] = []
    collected: dict[str, TestRecommendation] = {}

    ordered_rules = sorted(rules, key=lambda r: (-r.priority, r.name, r.rule_id))

    for rule in ordered_rules:
        try:
            fired = rule_matches(rule, facts)
        except RuleEvaluationError as exc:
            # A bad rule must not break the clinically essential path.
            logger.warning("Skipping invalid rule %s (%s): %s", rule.name, rule.rule_id, exc)
            invalid_ids.append(rule.rule_id)
            continue

        if not fired:
            continue

        matched_ids.append(rule.rule_id)
        for test in sorted(rule.tests, key=lambda t: (t.display_order, t.test_code)):
            key = test.test_code.strip().upper()
            if key in collected:
                continue
            collected[key] = TestRecommendation(
                test_code=test.test_code,
                test_name=test.test_name,
                reason_text=test.reason_text,
                rule_name=rule.name,
                priority=rule.priority,
                display_order=test.display_order,
            )

    tests = tuple(
        sorted(collected.values(), key=lambda t: (-t.priority, t.display_order, t.test_code))
    )
    return RecommendationOutcome(
        tests=tests,
        matched_rule_ids=tuple(matched_ids),
        general_recommendations=tuple(general_recommendations or ()),
        invalid_rule_ids=tuple(invalid_ids),
    )


def build_facts(
    *,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    district: Optional[str] = None,
    flow_type: Optional[str] = None,
    child_subtype: Optional[str] = None,
    answers: Optional[dict[str, str]] = None,
) -> dict[str, Any]:
    """
    Assemble the fact dictionary rules are evaluated against.

    Patient attributes and questionnaire answers share one namespace so a rule can
    combine them freely, e.g. age >= 60 AND sudden == yes. Answer keys win on
    collision, since a question explicitly asked about something is more specific
    than a registration field.
    """
    facts: dict[str, Any] = {}
    if age is not None:
        facts["age"] = age
    if gender:
        facts["gender"] = gender
    if district:
        facts["district"] = district
    if flow_type:
        facts["flow_type"] = flow_type
    if child_subtype:
        facts["child_subtype"] = child_subtype
    if answers:
        facts.update(answers)
    return facts


# General advice appended to every plan, by pathway. Editable content that is
# intentionally not test-specific.
GENERAL_ADULT: tuple[str, ...] = (
    "Avoid prolonged exposure to loud noise, and use ear protection where it is unavoidable.",
    "Do not insert cotton buds, oil or any object into the ear canal.",
    "Keep the ear dry if you have discharge or a known perforation.",
    "Attend the recommended tests before starting any treatment, so the plan is based on measurements.",
    "Bring a family member to your appointment if hearing difficulty makes conversation tiring.",
    "Report any sudden change in hearing, severe pain or dizziness immediately rather than waiting.",
)

GENERAL_CHILD: tuple[str, ...] = (
    "Talk, sing and read to your child through everyday routines — this is the strongest support you can give.",
    "Reduce background television and radio so speech is easier for your child to pick out.",
    "Complete the recommended tests before any conclusion is drawn about your child's hearing.",
    "If a hearing device is prescribed, consistent daily use matters more than anything else.",
    "Keep a note of what your child responds to at home and bring it to the appointment.",
    "Attend follow-up visits even if your child seems to be doing well, as hearing can change.",
    "Report ear discharge, fever or any sudden change in responsiveness without delay.",
)


def general_recommendations_for(flow_type: Optional[str]) -> tuple[str, ...]:
    return GENERAL_CHILD if flow_type == "child" else GENERAL_ADULT
