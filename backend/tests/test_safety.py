"""
Unit tests for the clinical safety net.

These are the highest-stakes tests in the suite: a false negative here means an
assistant chats through a medical emergency.
"""

from __future__ import annotations

import pytest

from app.models.enums import EscalationPriority
from app.services.safety import (
    EMERGENCY_MESSAGE,
    OUT_OF_SCOPE_MESSAGE,
    URGENT_MESSAGE,
    detect_red_flags,
    highest_priority,
    is_out_of_scope,
    safety_message_for,
    screen_message,
)


class TestDetectRedFlags:
    @pytest.mark.parametrize(
        "message,expected_code",
        [
            ("I woke up deaf in one ear this morning", "sudden_hearing_loss"),
            ("my hearing gone suddenly yesterday", "sudden_hearing_loss"),
            ("there is bleeding from ear after he hit my head", "acute_trauma"),
            ("my child has something stuck in ear", "acute_trauma"),
            ("I have facial weakness and ear pain", "neurological"),
            ("he keeps choking on every feed", "airway_swallowing"),
            ("baby is turning blue when feeding", "airway_swallowing"),
            ("I want to end my life", "self_harm"),
            ("there is pus and high fever", "acute_infection"),
            ("the room spinning and vomiting constantly", "acute_vertigo"),
        ],
    )
    def test_flags_are_detected(self, message, expected_code):
        codes = {f.code for f in detect_red_flags(message)}
        assert expected_code in codes

    @pytest.mark.parametrize(
        "message",
        [
            "What are your working hours?",
            "I would like to book a hearing test for my son",
            "My 3 year old is not speaking in full sentences",
            "How much does an audiogram cost?",
            "Can you explain what an OAE test is?",
        ],
    )
    def test_ordinary_messages_are_not_flagged(self, message):
        assert detect_red_flags(message) == []

    def test_detection_is_case_insensitive(self):
        assert detect_red_flags("SUDDEN HEARING LOSS in left ear")

    def test_multiple_flags_all_returned(self):
        flags = detect_red_flags("sudden hearing loss with high fever and pus")
        assert len(flags) >= 2

    def test_empty_input_is_safe(self):
        assert detect_red_flags("") == []
        assert detect_red_flags(None) == []


class TestHighestPriority:
    def test_emergency_wins_over_urgent(self):
        flags = detect_red_flags("sudden hearing loss with high fever and pus")
        assert highest_priority(flags) == EscalationPriority.EMERGENCY

    def test_urgent_when_only_urgent_flags(self):
        flags = detect_red_flags("there is pus and high fever")
        assert highest_priority(flags) == EscalationPriority.URGENT

    def test_none_when_no_flags(self):
        assert highest_priority([]) is None


class TestSafetyMessageFor:
    def test_each_priority_maps_to_its_fixed_message(self):
        assert safety_message_for(EscalationPriority.EMERGENCY) == EMERGENCY_MESSAGE
        assert safety_message_for(EscalationPriority.URGENT) == URGENT_MESSAGE
        assert safety_message_for(EscalationPriority.ROUTINE) == OUT_OF_SCOPE_MESSAGE

    def test_emergency_message_directs_to_in_person_care(self):
        assert "emergency" in EMERGENCY_MESSAGE.lower()


class TestIsOutOfScope:
    @pytest.mark.parametrize(
        "message",
        [
            "What medicine should I take for tinnitus?",
            "Can you prescribe something for the pain?",
            "What is the dosage for my child?",
            "Do I have hearing loss?",
            "Is it cancer?",
            "Please read my report and tell me what it means",
            "What does my audiogram mean?",
            "diagnose me please",
        ],
    )
    def test_clinical_requests_are_refused(self, message):
        assert is_out_of_scope(message)

    @pytest.mark.parametrize(
        "message",
        [
            "When will my report be ready?",
            "What documents do I need?",
            "Book me an appointment next week",
            "What happens during an ABR test?",
        ],
    )
    def test_legitimate_questions_are_allowed(self, message):
        assert not is_out_of_scope(message)


class TestScreenMessage:
    def test_red_flag_blocks_and_escalates(self):
        verdict = screen_message("I have sudden hearing loss since this morning")
        assert verdict.blocked
        assert verdict.escalate
        assert verdict.priority == EscalationPriority.EMERGENCY
        assert verdict.message == EMERGENCY_MESSAGE
        assert "sudden_hearing_loss" in verdict.trigger_codes

    def test_urgent_flag_uses_urgent_message(self):
        verdict = screen_message("severe ear pain and high fever")
        assert verdict.blocked
        assert verdict.escalate
        assert verdict.priority == EscalationPriority.URGENT
        assert verdict.message == URGENT_MESSAGE

    def test_out_of_scope_blocks_without_escalating(self):
        verdict = screen_message("what medicine should I take")
        assert verdict.blocked
        assert not verdict.escalate
        assert verdict.message == OUT_OF_SCOPE_MESSAGE

    def test_ordinary_message_passes_through(self):
        verdict = screen_message("I want to book a hearing test")
        assert not verdict.blocked
        assert not verdict.escalate
        assert verdict.message == ""
        assert verdict.trigger_codes == []

    def test_red_flag_takes_precedence_over_out_of_scope(self):
        # Mentions both medication and an emergency; the emergency must win.
        verdict = screen_message("what medicine for sudden hearing loss")
        assert verdict.escalate
        assert verdict.priority == EscalationPriority.EMERGENCY
