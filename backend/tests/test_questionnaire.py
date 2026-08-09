"""Unit tests for questionnaire traversal and branching."""

from __future__ import annotations

import pytest

from app.services.questionnaire import (
    OptionSnapshot,
    QuestionnaireError,
    QuestionSnapshot,
    entry_question,
    find_option,
    find_question,
    first_unanswered,
    ordered_options,
    ordered_questions,
    progress,
    resolve_next,
    validate_answer,
)


def _option(
    option_id: str,
    value: str = "yes",
    next_question_id: str | None = None,
    is_terminal: bool = False,
    order: int = 0,
) -> OptionSnapshot:
    return OptionSnapshot(
        option_id=option_id,
        label=value.title(),
        value=value,
        display_order=order,
        next_question_id=next_question_id,
        is_terminal=is_terminal,
    )


def _question(
    question_id: str,
    key: str,
    order: int,
    options: tuple[OptionSnapshot, ...] = (),
    is_entry: bool = False,
) -> QuestionSnapshot:
    return QuestionSnapshot(
        question_id=question_id,
        key=key,
        text=f"Question {key}?",
        display_order=order,
        options=options or (_option(f"{question_id}-a"),),
        is_entry=is_entry,
    )


# q1 -> branches: "yes" jumps to q3, "no" falls through to q2
FLOW = [
    _question(
        "q1",
        "sudden",
        0,
        options=(
            _option("o-yes", "yes", next_question_id="q3"),
            _option("o-no", "no"),
            _option("o-stop", "not_applicable", is_terminal=True),
        ),
        is_entry=True,
    ),
    _question("q2", "duration", 1),
    _question("q3", "side", 2),
]


class TestOrdering:
    def test_questions_sort_by_display_order(self):
        shuffled = [FLOW[2], FLOW[0], FLOW[1]]
        assert [q.key for q in ordered_questions(shuffled)] == ["sudden", "duration", "side"]

    def test_ties_break_on_key(self):
        a = _question("qa", "beta", 0)
        b = _question("qb", "alpha", 0)
        assert [q.key for q in ordered_questions([a, b])] == ["alpha", "beta"]

    def test_options_sort_by_display_order(self):
        question = _question(
            "q",
            "k",
            0,
            options=(_option("b", "second", order=1), _option("a", "first", order=0)),
        )
        assert [o.value for o in ordered_options(question)] == ["first", "second"]

    def test_empty_question_list_is_handled(self):
        assert ordered_questions([]) == []


class TestEntryQuestion:
    def test_explicit_entry_flag_wins(self):
        questions = [_question("q1", "later", 5, is_entry=True), _question("q2", "first", 0)]
        assert entry_question(questions).key == "later"

    def test_falls_back_to_lowest_display_order(self):
        questions = [_question("q2", "second", 1), _question("q1", "first", 0)]
        assert entry_question(questions).key == "first"

    def test_none_for_empty_flow(self):
        assert entry_question([]) is None


class TestLookups:
    def test_find_question_by_id(self):
        assert find_question(FLOW, "q2").key == "duration"

    def test_find_question_missing_returns_none(self):
        assert find_question(FLOW, "nope") is None
        assert find_question(FLOW, None) is None

    def test_find_option_by_id(self):
        assert find_option(FLOW[0], "o-yes").value == "yes"

    def test_find_option_missing_returns_none(self):
        assert find_option(FLOW[0], "nope") is None


class TestResolveNext:
    def test_branch_jumps_to_named_question(self):
        step = resolve_next(FLOW, FLOW[0], find_option(FLOW[0], "o-yes"))
        assert step.question.key == "side"
        assert step.reason == "branch"
        assert not step.is_complete

    def test_no_branch_falls_through_in_order(self):
        step = resolve_next(FLOW, FLOW[0], find_option(FLOW[0], "o-no"))
        assert step.question.key == "duration"
        assert step.reason == "sequential"

    def test_terminal_option_ends_the_flow(self):
        step = resolve_next(FLOW, FLOW[0], find_option(FLOW[0], "o-stop"))
        assert step.is_complete
        assert step.question is None
        assert step.reason == "terminal_option"

    def test_last_question_completes(self):
        step = resolve_next(FLOW, FLOW[2], find_option(FLOW[2], "q3-a"))
        assert step.is_complete
        assert step.reason == "end_of_flow"

    def test_already_answered_questions_are_skipped(self):
        step = resolve_next(FLOW, FLOW[0], find_option(FLOW[0], "o-no"), answered_question_ids=["q2"])
        assert step.question.key == "side"

    def test_completes_when_everything_else_is_answered(self):
        step = resolve_next(
            FLOW, FLOW[0], find_option(FLOW[0], "o-no"), answered_question_ids=["q2", "q3"]
        )
        assert step.is_complete

    def test_branch_to_deleted_question_falls_through(self):
        question = _question(
            "q1", "sudden", 0, options=(_option("o", "yes", next_question_id="ghost"),), is_entry=True
        )
        flow = [question, FLOW[1]]
        step = resolve_next(flow, question, question.options[0])
        assert step.question.key == "duration"
        assert step.reason == "branch_target_missing"

    def test_branch_to_answered_question_falls_through(self):
        step = resolve_next(
            FLOW, FLOW[0], find_option(FLOW[0], "o-yes"), answered_question_ids=["q3"]
        )
        assert step.question.key == "duration"
        assert step.reason == "branch_target_already_answered"

    def test_self_referencing_branch_cannot_loop(self):
        # An admin pointing a question at itself must not trap the patient.
        question = _question(
            "q1", "sudden", 0, options=(_option("o", "yes", next_question_id="q1"),), is_entry=True
        )
        flow = [question, FLOW[1]]
        step = resolve_next(flow, question, question.options[0])
        assert step.question is None or step.question.question_id != "q1"

    def test_mutual_branch_cycle_terminates(self):
        a = _question("qa", "a", 0, options=(_option("oa", "x", next_question_id="qb"),))
        b = _question("qb", "b", 1, options=(_option("ob", "y", next_question_id="qa"),))
        flow = [a, b]
        step = resolve_next(flow, b, b.options[0], answered_question_ids=["qa"])
        assert step.is_complete


class TestFirstUnanswered:
    def test_returns_earliest_unanswered(self):
        step = first_unanswered(FLOW, ["q1"])
        assert step.question.key == "duration"
        assert step.reason == "resume"

    def test_complete_when_all_answered(self):
        step = first_unanswered(FLOW, ["q1", "q2", "q3"])
        assert step.is_complete
        assert step.reason == "all_answered"

    def test_empty_answers_returns_entry(self):
        assert first_unanswered(FLOW, []).question.key == "sudden"


class TestProgress:
    def test_reports_answered_and_total(self):
        assert progress(FLOW, 2) == (2, 3)

    def test_clamps_answered_to_total(self):
        assert progress(FLOW, 9) == (3, 3)

    def test_empty_flow(self):
        assert progress([], 0) == (0, 0)


class TestValidateAnswer:
    def test_accepts_a_matching_pair(self):
        question, option = validate_answer(FLOW, "q1", "o-yes")
        assert question.key == "sudden"
        assert option.value == "yes"

    def test_rejects_unknown_question(self):
        with pytest.raises(QuestionnaireError):
            validate_answer(FLOW, "ghost", "o-yes")

    def test_rejects_option_from_another_question(self):
        with pytest.raises(QuestionnaireError):
            validate_answer(FLOW, "q2", "o-yes")
