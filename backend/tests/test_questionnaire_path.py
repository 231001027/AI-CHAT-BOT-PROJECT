"""
Tests for replaying a questionnaire after an answer is corrected.

The review screen lets a patient change an answer. When that answer controls a
branch, the questions that followed it may no longer apply, and their answers must
stop feeding the rule engine. These tests pin that behaviour down.
"""

from __future__ import annotations

from app.services.questionnaire import (
    OptionSnapshot,
    QuestionSnapshot,
    reachable_path,
)


def option(oid: str, value: str, *, branch: str | None = None, terminal: bool = False):
    return OptionSnapshot(
        option_id=oid,
        label=value.replace("_", " ").title(),
        value=value,
        display_order=0,
        next_question_id=branch,
        is_terminal=terminal,
    )


def question(qid: str, key: str, order: int, options, *, is_entry: bool = False):
    return QuestionSnapshot(
        question_id=qid,
        key=key,
        text=f"Question {key}?",
        display_order=order,
        options=tuple(options),
        is_entry=is_entry,
    )


def linear_flow():
    """q1 -> q2 -> q3, no branching."""
    return [
        question("q1", "first", 1, [option("o1a", "yes"), option("o1b", "no")], is_entry=True),
        question("q2", "second", 2, [option("o2a", "yes"), option("o2b", "no")]),
        question("q3", "third", 3, [option("o3a", "yes"), option("o3b", "no")]),
    ]


def branching_flow():
    """
    q1 routes to either the q2 branch or the q4 branch.

      q1 --left--> q2 -> q3 -> (end)
      q1 --both--> q4 -> (end)
    """
    return [
        question(
            "q1",
            "side",
            1,
            [option("o_left", "left", branch="q2"), option("o_both", "both", branch="q4")],
            is_entry=True,
        ),
        question("q2", "left_detail", 2, [option("o2a", "yes"), option("o2b", "no")]),
        question("q3", "left_extra", 3, [option("o3a", "yes", terminal=True)]),
        question("q4", "both_detail", 4, [option("o4a", "yes", terminal=True)]),
    ]


class TestReachablePathLinear:
    def test_no_answers_asks_the_entry_question(self):
        result = reachable_path(linear_flow(), {})
        assert result.next_question is not None
        assert result.next_question.key == "first"
        assert result.is_complete is False

    def test_partial_answers_resume_at_the_gap(self):
        result = reachable_path(linear_flow(), {"q1": "o1a"})
        assert result.next_question.key == "second"
        assert result.reachable_question_ids == ("q1", "q2")

    def test_all_answered_is_complete(self):
        result = reachable_path(linear_flow(), {"q1": "o1a", "q2": "o2a", "q3": "o3a"})
        assert result.is_complete is True
        assert result.next_question is None
        assert result.orphaned_question_ids == ()

    def test_route_is_in_encounter_order(self):
        result = reachable_path(linear_flow(), {"q1": "o1a", "q2": "o2a", "q3": "o3a"})
        assert result.reachable_question_ids == ("q1", "q2", "q3")

    def test_nothing_is_orphaned_without_branching(self):
        result = reachable_path(linear_flow(), {"q1": "o1a", "q2": "o2b"})
        assert result.orphaned_question_ids == ()


class TestReachablePathBranching:
    def test_left_branch_is_followed(self):
        result = reachable_path(branching_flow(), {"q1": "o_left"})
        assert result.next_question.key == "left_detail"
        assert "q4" not in result.reachable_question_ids

    def test_both_branch_is_followed(self):
        result = reachable_path(branching_flow(), {"q1": "o_both"})
        assert result.next_question.key == "both_detail"
        assert "q2" not in result.reachable_question_ids

    def test_switching_branch_orphans_the_abandoned_answers(self):
        # Patient answered the left branch fully, then changed q1 to "both".
        answers = {"q1": "o_both", "q2": "o2a", "q3": "o3a"}
        result = reachable_path(branching_flow(), answers)
        assert set(result.orphaned_question_ids) == {"q2", "q3"}
        assert result.next_question.key == "both_detail"

    def test_switching_back_reopens_the_original_branch(self):
        answers = {"q1": "o_left", "q4": "o4a"}
        result = reachable_path(branching_flow(), answers)
        assert set(result.orphaned_question_ids) == {"q4"}
        assert result.next_question.key == "left_detail"

    def test_terminal_option_completes_the_flow(self):
        result = reachable_path(branching_flow(), {"q1": "o_both", "q4": "o4a"})
        assert result.is_complete is True
        assert result.next_question is None

    def test_terminal_option_does_not_orphan_unreached_questions(self):
        # q2 and q3 were never answered, so they are not orphans — just unvisited.
        result = reachable_path(branching_flow(), {"q1": "o_both", "q4": "o4a"})
        assert result.orphaned_question_ids == ()

    def test_full_left_branch_completes(self):
        result = reachable_path(
            branching_flow(), {"q1": "o_left", "q2": "o2a", "q3": "o3a"}
        )
        assert result.is_complete is True
        assert result.reachable_question_ids == ("q1", "q2", "q3")


class TestReachablePathRobustness:
    def test_stale_option_id_forces_a_re_ask(self):
        # The option was deleted by an admin after the patient answered.
        result = reachable_path(linear_flow(), {"q1": "deleted-option"})
        assert result.next_question.key == "first"
        assert result.is_complete is False

    def test_empty_question_set_is_complete(self):
        result = reachable_path([], {})
        assert result.is_complete is True
        assert result.reachable_question_ids == ()

    def test_answers_for_unknown_questions_are_orphans(self):
        result = reachable_path(linear_flow(), {"q1": "o1a", "ghost": "gone"})
        assert "ghost" in result.orphaned_question_ids

    def test_a_cycle_terminates(self):
        # Authored content should never do this, but it must not hang.
        flow = [
            question("q1", "a", 1, [option("o1", "x", branch="q2")], is_entry=True),
            question("q2", "b", 2, [option("o2", "y", branch="q1")]),
        ]
        result = reachable_path(flow, {"q1": "o1", "q2": "o2"})
        assert result.is_complete is True

    def test_branch_to_a_missing_question_falls_through(self):
        flow = [
            question("q1", "a", 1, [option("o1", "x", branch="deleted")], is_entry=True),
            question("q2", "b", 2, [option("o2", "y")]),
        ]
        result = reachable_path(flow, {"q1": "o1"})
        assert result.next_question.key == "b"

    def test_is_deterministic(self):
        answers = {"q1": "o_left", "q2": "o2a"}
        first = reachable_path(branching_flow(), answers)
        second = reachable_path(branching_flow(), answers)
        assert first == second
