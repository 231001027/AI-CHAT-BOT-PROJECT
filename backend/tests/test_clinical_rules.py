"""Unit tests for the deterministic clinical rule engine."""

from __future__ import annotations

import pytest

from app.services.clinical_rules import (
    RuleEvaluationError,
    RuleSnapshot,
    TestRecommendation,
    build_facts,
    evaluate_leaf,
    evaluate_predicate,
    general_recommendations_for,
    recommend_tests,
    rule_matches,
)

FACTS = {
    "age": 65,
    "gender": "male",
    "flow_type": "adult",
    "sudden": "yes",
    "duration_months": "8",
    "side": "left",
    "tinnitus": "no",
    "noise_exposure": "",
}


def _test(code: str = "PTA", order: int = 0) -> TestRecommendation:
    return TestRecommendation(
        test_code=code,
        test_name=f"{code} test",
        reason_text=f"Because of {code}",
        rule_name="r",
        display_order=order,
    )


def _rule(
    rule_id: str = "r1",
    definition: dict | None = None,
    tests: tuple[TestRecommendation, ...] = (),
    priority: int = 0,
    is_baseline: bool = False,
    name: str = "Rule",
) -> RuleSnapshot:
    return RuleSnapshot(
        rule_id=rule_id,
        name=name,
        rule_definition=definition if definition is not None else {},
        tests=tests or (_test(),),
        priority=priority,
        is_baseline=is_baseline,
    )


class TestEvaluateLeaf:
    @pytest.mark.parametrize(
        "node,expected",
        [
            ({"field": "sudden", "op": "eq", "value": "yes"}, True),
            ({"field": "sudden", "op": "eq", "value": "no"}, False),
            ({"field": "sudden", "op": "ne", "value": "no"}, True),
            ({"field": "age", "op": ">", "value": 60}, True),
            ({"field": "age", "op": ">", "value": 70}, False),
            ({"field": "age", "op": ">=", "value": 65}, True),
            ({"field": "age", "op": "<", "value": 70}, True),
            ({"field": "age", "op": "<=", "value": 64}, False),
            ({"field": "side", "op": "in", "value": ["left", "both"]}, True),
            ({"field": "side", "op": "in", "value": ["right"]}, False),
            ({"field": "side", "op": "not_in", "value": ["right"]}, True),
            ({"field": "gender", "op": "contains", "value": "MAL"}, True),
            ({"field": "sudden", "op": "exists"}, True),
            ({"field": "absent_field", "op": "exists"}, False),
            ({"field": "sudden", "op": "truthy"}, True),
            ({"field": "tinnitus", "op": "truthy"}, False),
            ({"field": "tinnitus", "op": "falsy"}, True),
            ({"field": "noise_exposure", "op": "truthy"}, False),
        ],
    )
    def test_operators(self, node, expected):
        assert evaluate_leaf(node, FACTS) is expected

    def test_string_answer_compares_numerically(self):
        # duration_months arrives from a form as the string "8"
        assert evaluate_leaf({"field": "duration_months", "op": ">", "value": 6}, FACTS)
        assert not evaluate_leaf({"field": "duration_months", "op": ">", "value": 12}, FACTS)

    def test_case_insensitive_equality(self):
        assert evaluate_leaf({"field": "gender", "op": "eq", "value": "MALE"}, FACTS)

    def test_missing_field_is_false_not_an_error(self):
        assert not evaluate_leaf({"field": "nope", "op": "eq", "value": "x"}, FACTS)
        assert not evaluate_leaf({"field": "nope", "op": ">", "value": 1}, FACTS)

    def test_missing_field_name_raises(self):
        with pytest.raises(RuleEvaluationError):
            evaluate_leaf({"op": "eq", "value": "x"}, FACTS)

    def test_unknown_operator_raises(self):
        with pytest.raises(RuleEvaluationError):
            evaluate_leaf({"field": "age", "op": "approximately", "value": 60}, FACTS)

    def test_in_without_a_list_raises(self):
        with pytest.raises(RuleEvaluationError):
            evaluate_leaf({"field": "side", "op": "in", "value": "left"}, FACTS)

    def test_incomparable_types_are_false(self):
        assert not evaluate_leaf({"field": "gender", "op": ">", "value": 5}, FACTS)


class TestEvaluatePredicate:
    def test_all_requires_every_child(self):
        node = {"all": [{"field": "sudden", "op": "eq", "value": "yes"}, {"field": "age", "op": ">", "value": 60}]}
        assert evaluate_predicate(node, FACTS)

    def test_all_fails_if_one_child_fails(self):
        node = {"all": [{"field": "sudden", "op": "eq", "value": "yes"}, {"field": "age", "op": ">", "value": 90}]}
        assert not evaluate_predicate(node, FACTS)

    def test_any_needs_only_one_child(self):
        node = {"any": [{"field": "age", "op": ">", "value": 90}, {"field": "side", "op": "eq", "value": "left"}]}
        assert evaluate_predicate(node, FACTS)

    def test_any_fails_when_no_child_matches(self):
        node = {"any": [{"field": "age", "op": ">", "value": 90}, {"field": "side", "op": "eq", "value": "right"}]}
        assert not evaluate_predicate(node, FACTS)

    def test_not_inverts(self):
        assert evaluate_predicate({"not": {"field": "tinnitus", "op": "eq", "value": "yes"}}, FACTS)

    def test_nested_tree(self):
        node = {
            "all": [
                {"field": "sudden", "op": "eq", "value": "yes"},
                {
                    "any": [
                        {"field": "age", "op": ">=", "value": 60},
                        {"field": "noise_exposure", "op": "truthy"},
                    ]
                },
                {"not": {"field": "side", "op": "eq", "value": "right"}},
            ]
        }
        assert evaluate_predicate(node, FACTS)

    def test_empty_definition_never_matches(self):
        assert not evaluate_predicate({}, FACTS)

    def test_empty_all_never_matches(self):
        # An empty 'all' is vacuously true in logic, but for a clinical rule it
        # means "misconfigured", so it must not fire for every patient.
        assert not evaluate_predicate({"all": []}, FACTS)

    def test_empty_any_never_matches(self):
        assert not evaluate_predicate({"any": []}, FACTS)

    def test_non_dict_node_never_matches(self):
        assert not evaluate_predicate(None, FACTS)
        assert not evaluate_predicate("yes", FACTS)

    def test_malformed_branch_raises(self):
        with pytest.raises(RuleEvaluationError):
            evaluate_predicate({"all": {"field": "age"}}, FACTS)


class TestRuleMatches:
    def test_baseline_rule_always_fires(self):
        assert rule_matches(_rule(definition={}, is_baseline=True), FACTS)
        assert rule_matches(_rule(definition={}, is_baseline=True), {})

    def test_conditional_rule_respects_its_definition(self):
        rule = _rule(definition={"field": "sudden", "op": "eq", "value": "yes"})
        assert rule_matches(rule, FACTS)
        assert not rule_matches(rule, {"sudden": "no"})


class TestRecommendTests:
    def test_collects_tests_from_matching_rules(self):
        rules = [
            _rule("r1", {"field": "sudden", "op": "eq", "value": "yes"}, (_test("PTA"),)),
            _rule("r2", {"field": "age", "op": ">", "value": 60}, (_test("OAE"),)),
        ]
        outcome = recommend_tests(rules, FACTS)
        assert [t.test_code for t in outcome.tests] == ["OAE", "PTA"]
        assert set(outcome.matched_rule_ids) == {"r1", "r2"}

    def test_ignores_non_matching_rules(self):
        rules = [_rule("r1", {"field": "sudden", "op": "eq", "value": "no"}, (_test("PTA"),))]
        outcome = recommend_tests(rules, FACTS)
        assert outcome.tests == ()
        assert outcome.matched_rule_ids == ()

    def test_deduplicates_by_test_code(self):
        rules = [
            _rule("r1", {"field": "sudden", "op": "eq", "value": "yes"}, (_test("PTA"),), priority=5),
            _rule("r2", {"field": "age", "op": ">", "value": 60}, (_test("pta"),), priority=1),
        ]
        outcome = recommend_tests(rules, FACTS)
        assert len(outcome.tests) == 1

    def test_highest_priority_rule_owns_the_reason(self):
        high = RuleSnapshot(
            rule_id="high",
            name="High",
            rule_definition={"field": "sudden", "op": "eq", "value": "yes"},
            tests=(TestRecommendation("PTA", "PTA", "urgent reason", "High"),),
            priority=10,
        )
        low = RuleSnapshot(
            rule_id="low",
            name="Low",
            rule_definition={"field": "age", "op": ">", "value": 60},
            tests=(TestRecommendation("PTA", "PTA", "routine reason", "Low"),),
            priority=1,
        )
        outcome = recommend_tests([low, high], FACTS)
        assert outcome.tests[0].reason_text == "urgent reason"
        assert outcome.tests[0].rule_name == "High"

    def test_orders_by_priority_descending(self):
        rules = [
            _rule("low", {"field": "sudden", "op": "truthy"}, (_test("LOW"),), priority=1),
            _rule("high", {"field": "sudden", "op": "truthy"}, (_test("HIGH"),), priority=9),
        ]
        outcome = recommend_tests(rules, FACTS)
        assert [t.test_code for t in outcome.tests] == ["HIGH", "LOW"]

    def test_baseline_tests_are_always_present(self):
        rules = [_rule("base", {}, (_test("PTA"),), is_baseline=True)]
        outcome = recommend_tests(rules, {})
        assert [t.test_code for t in outcome.tests] == ["PTA"]

    def test_invalid_rule_is_skipped_not_fatal(self):
        rules = [
            _rule("bad", {"field": "age", "op": "nonsense", "value": 1}, (_test("BAD"),)),
            _rule("good", {"field": "sudden", "op": "eq", "value": "yes"}, (_test("GOOD"),)),
        ]
        outcome = recommend_tests(rules, FACTS)
        assert [t.test_code for t in outcome.tests] == ["GOOD"]
        assert outcome.invalid_rule_ids == ("bad",)

    def test_general_recommendations_pass_through(self):
        outcome = recommend_tests([], FACTS, general_recommendations=["a", "b"])
        assert outcome.general_recommendations == ("a", "b")

    def test_no_rules_yields_empty_outcome(self):
        outcome = recommend_tests([], FACTS)
        assert outcome.tests == ()
        assert outcome.matched_rule_ids == ()

    def test_result_is_deterministic(self):
        rules = [
            _rule("r1", {"field": "sudden", "op": "truthy"}, (_test("A"), _test("B", order=1))),
            _rule("r2", {"field": "age", "op": ">", "value": 1}, (_test("C"),)),
        ]
        first = [t.test_code for t in recommend_tests(rules, FACTS).tests]
        second = [t.test_code for t in recommend_tests(rules, FACTS).tests]
        assert first == second


class TestBuildFacts:
    def test_merges_patient_fields_and_answers(self):
        facts = build_facts(age=40, gender="female", flow_type="adult", answers={"sudden": "yes"})
        assert facts == {"age": 40, "gender": "female", "flow_type": "adult", "sudden": "yes"}

    def test_omits_missing_values(self):
        assert build_facts(age=None, gender=None) == {}

    def test_answers_override_patient_fields(self):
        facts = build_facts(age=40, answers={"age": "12"})
        assert facts["age"] == "12"

    def test_child_subtype_included(self):
        facts = build_facts(flow_type="child", child_subtype="newborn")
        assert facts["child_subtype"] == "newborn"


class TestGeneralRecommendations:
    def test_child_flow_gets_child_advice(self):
        advice = general_recommendations_for("child")
        assert any("read to your child" in a for a in advice)

    def test_adult_flow_gets_adult_advice(self):
        advice = general_recommendations_for("adult")
        assert any("loud noise" in a for a in advice)

    def test_unknown_flow_defaults_to_adult(self):
        assert general_recommendations_for(None) == general_recommendations_for("adult")

    def test_advice_is_never_empty(self):
        for flow in ("adult", "child", None):
            assert general_recommendations_for(flow)
