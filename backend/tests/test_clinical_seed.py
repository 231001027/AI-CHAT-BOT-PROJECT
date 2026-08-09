"""
Integrity tests for the seeded clinical content.

These catch the failure modes that would otherwise only show up as a patient
getting the wrong tests or a flow dead-ending: a rule referencing a question key
that does not exist, a branch pointing outside its condition, or a condition with
no entry question.
"""

from __future__ import annotations

import pytest

from app.models.enums import FlowType
from app.services.clinical_rules import (
    RuleEvaluationError,
    RuleSnapshot,
    TestRecommendation,
    evaluate_predicate,
    recommend_tests,
)
from app.services.clinical_seed_data import CATEGORIES, CONDITIONS, QUESTIONS, RULES

CATEGORY_SLUGS = {c["slug"] for c in CATEGORIES}
CONDITION_SLUGS = {c["slug"] for c in CONDITIONS}


def _keys_for(condition_slug: str) -> set[str]:
    return {q["key"] for q in QUESTIONS if q["condition_slug"] == condition_slug}


def _questions_for(condition_slug: str) -> list[dict]:
    return [q for q in QUESTIONS if q["condition_slug"] == condition_slug]


class TestCategories:
    def test_slugs_are_unique(self):
        slugs = [c["slug"] for c in CATEGORIES]
        assert len(slugs) == len(set(slugs))

    def test_flow_types_are_valid(self):
        valid = {f.value for f in FlowType}
        assert all(c["flow_type"] in valid for c in CATEGORIES)

    def test_both_pathways_have_categories(self):
        flows = {c["flow_type"] for c in CATEGORIES}
        assert flows == {FlowType.ADULT.value, FlowType.CHILD.value}

    def test_every_category_has_a_description(self):
        assert all(c["description"].strip() for c in CATEGORIES)


class TestConditions:
    def test_slugs_are_unique(self):
        slugs = [c["slug"] for c in CONDITIONS]
        assert len(slugs) == len(set(slugs))

    def test_every_condition_belongs_to_a_real_category(self):
        for condition in CONDITIONS:
            assert condition["category_slug"] in CATEGORY_SLUGS, condition["slug"]

    def test_every_category_has_at_least_one_condition(self):
        used = {c["category_slug"] for c in CONDITIONS}
        assert used == CATEGORY_SLUGS, f"categories with no conditions: {CATEGORY_SLUGS - used}"


class TestQuestions:
    def test_every_question_belongs_to_a_real_condition(self):
        for question in QUESTIONS:
            assert question["condition_slug"] in CONDITION_SLUGS, question["key"]

    def test_every_condition_has_questions(self):
        for slug in CONDITION_SLUGS:
            assert _questions_for(slug), f"condition {slug} has no questions"

    def test_every_condition_has_exactly_one_entry_question(self):
        for slug in CONDITION_SLUGS:
            entries = [q for q in _questions_for(slug) if q.get("is_entry")]
            assert len(entries) == 1, f"{slug} has {len(entries)} entry questions"

    def test_keys_are_unique_within_a_condition(self):
        for slug in CONDITION_SLUGS:
            keys = [q["key"] for q in _questions_for(slug)]
            assert len(keys) == len(set(keys)), f"duplicate keys in {slug}"

    def test_display_orders_are_unique_within_a_condition(self):
        for slug in CONDITION_SLUGS:
            orders = [q["display_order"] for q in _questions_for(slug)]
            assert len(orders) == len(set(orders)), f"duplicate display_order in {slug}"

    def test_every_question_has_at_least_two_options(self):
        for question in QUESTIONS:
            options = question.get("options", [])
            assert len(options) >= 2, f"{question['key']} has {len(options)} options"

    def test_option_values_are_unique_within_a_question(self):
        for question in QUESTIONS:
            values = [o["value"] for o in question.get("options", [])]
            assert len(values) == len(set(values)), f"duplicate values in {question['key']}"

    def test_option_values_are_machine_safe(self):
        # Rules match on these, so they must not contain spaces or punctuation.
        for question in QUESTIONS:
            for option in question.get("options", []):
                value = option["value"]
                assert value.replace("_", "").replace(".", "").isalnum(), (
                    f"{question['key']} has unsafe option value {value!r}"
                )

    def test_every_option_has_a_label(self):
        for question in QUESTIONS:
            for option in question.get("options", []):
                assert option["label"].strip(), f"empty label in {question['key']}"

    def test_branch_targets_exist_within_the_same_condition(self):
        for question in QUESTIONS:
            slug = question["condition_slug"]
            available = _keys_for(slug)
            for option in question.get("options", []):
                target = option.get("branch")
                if target:
                    assert target in available, (
                        f"{question['key']} branches to '{target}', "
                        f"which is not in condition {slug}"
                    )

    def test_no_option_branches_to_its_own_question(self):
        for question in QUESTIONS:
            for option in question.get("options", []):
                assert option.get("branch") != question["key"], (
                    f"{question['key']} branches to itself"
                )

    def test_branches_move_forward(self):
        # A backwards branch is legal (the traversal skips answered questions) but
        # is almost always a mistake in authored content.
        by_key = {(q["condition_slug"], q["key"]): q for q in QUESTIONS}
        for question in QUESTIONS:
            for option in question.get("options", []):
                target_key = option.get("branch")
                if not target_key:
                    continue
                target = by_key[(question["condition_slug"], target_key)]
                assert target["display_order"] > question["display_order"], (
                    f"{question['key']} branches backwards to {target_key}"
                )


class TestRules:
    def test_every_rule_targets_a_real_condition(self):
        for rule in RULES:
            assert rule["condition_slug"] in CONDITION_SLUGS, rule["name"]

    def test_rule_names_are_unique(self):
        names = [r["name"] for r in RULES]
        assert len(names) == len(set(names))

    def test_every_condition_has_a_baseline_rule(self):
        # Without a baseline, a patient whose answers match no conditional rule
        # would receive an empty recommendation list.
        for slug in CONDITION_SLUGS:
            baselines = [
                r for r in RULES if r["condition_slug"] == slug and r.get("is_baseline")
            ]
            assert len(baselines) == 1, f"{slug} has {len(baselines)} baseline rules"

    def test_every_rule_recommends_at_least_one_test(self):
        for rule in RULES:
            assert rule.get("tests"), f"rule '{rule['name']}' recommends nothing"

    def test_every_test_has_a_code_name_and_reason(self):
        for rule in RULES:
            for test in rule["tests"]:
                assert test["test_code"].strip(), rule["name"]
                assert test["test_name"].strip(), rule["name"]
                # The reason is shown to the patient, so it must not be blank.
                assert test["reason_text"].strip(), f"{rule['name']} / {test['test_code']}"

    def test_conditional_rules_have_a_definition(self):
        for rule in RULES:
            if not rule.get("is_baseline"):
                assert rule.get("rule_definition"), (
                    f"'{rule['name']}' is not baseline but has no definition, so it never fires"
                )

    def test_baseline_rules_have_an_empty_definition(self):
        for rule in RULES:
            if rule.get("is_baseline"):
                assert not rule.get("rule_definition"), (
                    f"'{rule['name']}' is baseline, so its definition would be ignored"
                )

    def test_every_definition_is_structurally_valid(self):
        for rule in RULES:
            try:
                evaluate_predicate(rule.get("rule_definition") or {}, {})
            except RuleEvaluationError as exc:
                pytest.fail(f"rule '{rule['name']}' is invalid: {exc}")

    def test_rules_only_reference_known_fields(self):
        """
        Every field a rule matches on must be a question key in the same
        condition, or a patient attribute. A typo here means the rule silently
        never fires.
        """
        patient_fields = {"age", "gender", "district", "flow_type", "child_subtype"}

        def collect(node, found: set[str]) -> None:
            if not isinstance(node, dict):
                return
            if "field" in node:
                found.add(node["field"])
            for key in ("all", "any"):
                for child in node.get(key, []) or []:
                    collect(child, found)
            if "not" in node:
                collect(node["not"], found)

        for rule in RULES:
            fields: set[str] = set()
            collect(rule.get("rule_definition") or {}, fields)
            allowed = _keys_for(rule["condition_slug"]) | patient_fields
            unknown = fields - allowed
            assert not unknown, f"rule '{rule['name']}' references unknown fields {unknown}"

    def test_rule_values_match_declared_options(self):
        """
        A rule comparing against a value no option can produce would never fire.
        Only checked for equality and membership on non-numeric values, since
        numeric thresholds legitimately fall between option values.
        """
        options_by_key: dict[tuple[str, str], set[str]] = {}
        for question in QUESTIONS:
            key = (question["condition_slug"], question["key"])
            options_by_key[key] = {o["value"] for o in question.get("options", [])}

        def check(node, condition_slug: str) -> None:
            if not isinstance(node, dict):
                return
            for branch in ("all", "any"):
                for child in node.get(branch, []) or []:
                    check(child, condition_slug)
            if "not" in node:
                check(node["not"], condition_slug)

            field = node.get("field")
            if not field or node.get("op") not in {"eq", "in", None}:
                return
            available = options_by_key.get((condition_slug, field))
            if available is None:
                return  # patient attribute, not a question

            expected = node.get("value")
            candidates = expected if isinstance(expected, list) else [expected]
            for candidate in candidates:
                if candidate is None or str(candidate).replace(".", "").isdigit():
                    continue
                assert str(candidate) in available, (
                    f"condition {condition_slug}: field '{field}' compared against "
                    f"{candidate!r}, which is not one of {sorted(available)}"
                )

        for rule in RULES:
            check(rule.get("rule_definition") or {}, rule["condition_slug"])


class TestSeedRulesEndToEnd:
    """Run the real seeded rules through the engine for representative patients."""

    @staticmethod
    def _snapshots(condition_slug: str) -> list[RuleSnapshot]:
        return [
            RuleSnapshot(
                rule_id=rule["name"],
                name=rule["name"],
                rule_definition=rule.get("rule_definition") or {},
                priority=rule.get("priority", 0),
                is_baseline=rule.get("is_baseline", False),
                tests=tuple(
                    TestRecommendation(
                        test_code=t["test_code"],
                        test_name=t["test_name"],
                        reason_text=t["reason_text"],
                        rule_name=rule["name"],
                        priority=rule.get("priority", 0),
                        display_order=t.get("display_order", 0),
                    )
                    for t in rule["tests"]
                ),
            )
            for rule in RULES
            if rule["condition_slug"] == condition_slug
        ]

    def test_baseline_only_patient_still_gets_tests(self):
        # No answers at all: the baseline rule must carry the flow.
        outcome = recommend_tests(self._snapshots("adult-hearing-difficulty-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "PTA" in codes

    def test_adult_ringing_baseline_includes_tinnitus_assessment(self):
        outcome = recommend_tests(self._snapshots("adult-ringing-ears-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "PTA" in codes and "TINN_ASSESS" in codes

    def test_adult_dizziness_baseline_includes_balance_screen(self):
        outcome = recommend_tests(self._snapshots("adult-dizziness-balance-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "PTA" in codes and "VNG" in codes

    def test_adult_ear_pain_baseline_prioritises_middle_ear(self):
        outcome = recommend_tests(self._snapshots("adult-ear-pain-discharge-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "TYMP" in codes and "OTOSCOPY" in codes

    def test_adult_speech_language_baseline_includes_hearing_screen(self):
        outcome = recommend_tests(self._snapshots("adult-speech-language-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "SLP_EVAL" in codes
        assert "PTA" in codes

    def test_adult_voice_baseline_includes_voice_eval(self):
        outcome = recommend_tests(self._snapshots("adult-voice-screen"), {})
        assert "VOICE_EVAL" in {t.test_code for t in outcome.tests}

    def test_adult_swallowing_baseline_includes_swallow_assessment(self):
        outcome = recommend_tests(self._snapshots("adult-feeding-swallowing-screen"), {})
        assert "SWALLOW_ASSESS" in {t.test_code for t in outcome.tests}

    def test_adult_stuttering_baseline_includes_fluency_eval(self):
        outcome = recommend_tests(self._snapshots("adult-stuttering-fluency"), {})
        assert "FLUENCY_EVAL" in {t.test_code for t in outcome.tests}

    def test_child_speech_language_baseline_includes_hearing_screen(self):
        outcome = recommend_tests(self._snapshots("child-speech-language-issues"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "SLP_EVAL" in codes
        assert "OAE" in codes

    def test_child_hearing_difficulty_baseline_includes_hearing_battery(self):
        outcome = recommend_tests(self._snapshots("child-hearing-difficulty-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "PTA" in codes and "TYMP" in codes and "OAE" in codes

    def test_child_ear_pain_baseline_prioritises_middle_ear(self):
        outcome = recommend_tests(self._snapshots("child-ear-pain-discharge-screen"), {})
        codes = {t.test_code for t in outcome.tests}
        assert "TYMP" in codes and "OTOSCOPY" in codes

    def test_child_stuttering_baseline_includes_fluency_eval(self):
        outcome = recommend_tests(self._snapshots("child-stuttering-fluency"), {})
        assert "FLUENCY_EVAL" in {t.test_code for t in outcome.tests}

    def test_child_feeding_baseline_includes_swallow_assessment(self):
        outcome = recommend_tests(self._snapshots("child-feeding-swallowing-issues"), {})
        assert "SWALLOW_ASSESS" in {t.test_code for t in outcome.tests}

    def test_no_seeded_rule_set_ever_returns_empty(self):
        for slug in CONDITION_SLUGS:
            outcome = recommend_tests(self._snapshots(slug), {})
            assert outcome.tests, f"condition {slug} produces no tests for a blank patient"

    def test_no_invalid_rules_at_runtime(self):
        for slug in CONDITION_SLUGS:
            outcome = recommend_tests(self._snapshots(slug), {"age": 40})
            assert outcome.invalid_rule_ids == (), f"{slug} has invalid rules"
