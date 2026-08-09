"""
Questionnaire traversal.

Pure, database-free logic for deciding which question comes next, kept separate
from the route layer so branching can be unit-tested without a session.

Branching precedence, highest first:
  1. The selected option is terminal -> the questionnaire ends.
  2. The selected option names an explicit next_question_id -> go there.
  3. Otherwise fall through to the next active question by display_order.

A question already answered in this pass is never served again, which stops a
cycle in admin-authored branching from trapping a patient in a loop.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Optional, Sequence


@dataclass(frozen=True)
class OptionSnapshot:
    option_id: str
    label: str
    value: str
    display_order: int = 0
    next_question_id: Optional[str] = None
    is_terminal: bool = False


@dataclass(frozen=True)
class QuestionSnapshot:
    question_id: str
    key: str
    text: str
    display_order: int
    options: tuple[OptionSnapshot, ...]
    question_type: str = "single_select"
    help_text: Optional[str] = None
    is_entry: bool = False


@dataclass(frozen=True)
class NextStep:
    """Either the next question to ask, or completion."""

    question: Optional[QuestionSnapshot]
    is_complete: bool
    reason: str = ""


class QuestionnaireError(ValueError):
    """Raised when an answer references something outside the current flow."""


def ordered_questions(questions: Sequence[QuestionSnapshot]) -> list[QuestionSnapshot]:
    """Deterministic ordering: display_order, then key as a stable tiebreak."""
    return sorted(questions, key=lambda q: (q.display_order, q.key))


def entry_question(questions: Sequence[QuestionSnapshot]) -> Optional[QuestionSnapshot]:
    """
    The first question of a flow.

    An explicit ``is_entry`` flag wins; otherwise the lowest display_order. This
    lets admins reorder a question set without accidentally changing where the
    flow starts.
    """
    ordered = ordered_questions(questions)
    if not ordered:
        return None
    return next((q for q in ordered if q.is_entry), ordered[0])


def find_question(
    questions: Sequence[QuestionSnapshot], question_id: Optional[str]
) -> Optional[QuestionSnapshot]:
    if not question_id:
        return None
    return next((q for q in questions if q.question_id == question_id), None)


def find_option(question: QuestionSnapshot, option_id: str) -> Optional[OptionSnapshot]:
    return next((o for o in question.options if o.option_id == option_id), None)


def ordered_options(question: QuestionSnapshot) -> list[OptionSnapshot]:
    return sorted(question.options, key=lambda o: (o.display_order, o.label))


def resolve_next(
    questions: Sequence[QuestionSnapshot],
    current: QuestionSnapshot,
    selected: OptionSnapshot,
    answered_question_ids: Sequence[str] = (),
) -> NextStep:
    """
    Decide what follows an answer.

    ``answered_question_ids`` should include the question just answered; it is
    used to skip anything already covered.
    """
    seen = set(answered_question_ids) | {current.question_id}

    if selected.is_terminal:
        return NextStep(question=None, is_complete=True, reason="terminal_option")

    if selected.next_question_id:
        target = find_question(questions, selected.next_question_id)
        if target is None:
            # The branch points at a deleted question. Fall through rather than
            # dead-end the patient, and let the admin screens surface the gap.
            return _fall_through(questions, current, seen, reason="branch_target_missing")
        if target.question_id in seen:
            return _fall_through(questions, current, seen, reason="branch_target_already_answered")
        return NextStep(question=target, is_complete=False, reason="branch")

    return _fall_through(questions, current, seen, reason="sequential")


def _fall_through(
    questions: Sequence[QuestionSnapshot],
    current: QuestionSnapshot,
    seen: set[str],
    *,
    reason: str,
) -> NextStep:
    """Advance to the next unanswered question after ``current`` by order."""
    for question in ordered_questions(questions):
        if question.question_id in seen:
            continue
        if (question.display_order, question.key) > (current.display_order, current.key):
            return NextStep(question=question, is_complete=False, reason=reason)

    return NextStep(question=None, is_complete=True, reason="end_of_flow")


def first_unanswered(
    questions: Sequence[QuestionSnapshot], answered_question_ids: Sequence[str]
) -> NextStep:
    """
    Resume a partially completed pass.

    Used when a session is reopened and the stored current question is gone.
    """
    seen = set(answered_question_ids)
    for question in ordered_questions(questions):
        if question.question_id not in seen:
            return NextStep(question=question, is_complete=False, reason="resume")
    return NextStep(question=None, is_complete=True, reason="all_answered")


@dataclass(frozen=True)
class PathResult:
    """The questions actually on a patient's route, given their current answers."""

    # Ordered as the patient encountered them.
    reachable_question_ids: tuple[str, ...]
    # Answered questions no longer on the route, because a branch changed.
    orphaned_question_ids: tuple[str, ...]
    next_question: Optional[QuestionSnapshot]
    is_complete: bool


def reachable_path(
    questions: Sequence[QuestionSnapshot],
    answers: Mapping[str, str],
) -> PathResult:
    """
    Replay a questionnaire from the entry point using the answers given.

    Needed when a patient edits an answer on the review screen. Changing a
    branching answer can make previously answered questions unreachable, and those
    stale answers must not keep feeding the rule engine — a patient who switched
    "left ear" to "both ears" should not still be carrying the follow-up answers
    from the one-sided branch.

    ``answers`` maps question_id to the chosen option_id. Pure and terminating:
    each question is visited at most once.
    """
    route: list[str] = []
    current = entry_question(questions)
    is_complete = False
    next_question: Optional[QuestionSnapshot] = None

    while current is not None:
        if current.question_id in route:
            break  # Defensive: authored content should never cycle.
        route.append(current.question_id)

        chosen_option_id = answers.get(current.question_id)
        if chosen_option_id is None:
            next_question = current
            break

        option = find_option(current, chosen_option_id)
        if option is None:
            # The stored option no longer exists on this question, so the answer
            # cannot be trusted to route. Stop here and re-ask.
            next_question = current
            break

        step = resolve_next(questions, current, option, answered_question_ids=route)
        if step.is_complete or step.question is None:
            is_complete = True
            break
        current = step.question
    else:
        is_complete = True

    reachable = set(route)
    orphaned = tuple(qid for qid in answers if qid not in reachable)

    # A question is only truly answered if it is on the route.
    return PathResult(
        reachable_question_ids=tuple(route),
        orphaned_question_ids=orphaned,
        next_question=next_question,
        is_complete=is_complete and next_question is None,
    )


def progress(questions: Sequence[QuestionSnapshot], answered_count: int) -> tuple[int, int]:
    """
    Answered count and a total for the progress indicator.

    With branching the true remaining count is unknowable up front, so the total
    is the size of the question set — an upper bound. It is clamped so the
    indicator never shows more answered than total.
    """
    total = len(questions)
    return min(answered_count, total), total


def validate_answer(
    questions: Sequence[QuestionSnapshot], question_id: str, option_id: str
) -> tuple[QuestionSnapshot, OptionSnapshot]:
    """
    Check an answer belongs to this flow before it is persisted.

    Guards against a client posting an option that belongs to another question.
    """
    question = find_question(questions, question_id)
    if question is None:
        raise QuestionnaireError("That question is not part of this questionnaire.")

    option = find_option(question, option_id)
    if option is None:
        raise QuestionnaireError("That option does not belong to the question being answered.")

    return question, option
