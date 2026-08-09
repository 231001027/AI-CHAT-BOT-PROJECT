"""
Deterministic clinical safety net for the assistant suite.

Runs BEFORE any LLM call. If a red flag is present the assistant is bypassed
entirely and the patient receives a fixed, clinician-approved message plus an
escalation ticket. This is intentionally keyword-based and conservative: false
positives cost a staff callback, false negatives cost a patient.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from app.models.enums import EscalationPriority

# Fixed responses. These are never rephrased by the LLM.
EMERGENCY_MESSAGE = (
    "This needs urgent in-person medical attention — please do not wait for an "
    "online reply. Go to the nearest emergency department or ENT casualty now, or "
    "call the NIEPMD helpline on 044-2452-0639 during working hours. "
    "I have flagged this conversation for our clinical team."
)

URGENT_MESSAGE = (
    "What you have described should be reviewed by a clinician soon rather than "
    "handled over chat. I have flagged this for our department so a staff member "
    "can contact you, and you can also call 044-2452-0639 during working hours "
    "(Monday–Friday, 9:00 AM–5:00 PM)."
)

# Requests the assistants must always refuse, whatever the phrasing.
OUT_OF_SCOPE_MESSAGE = (
    "I am not able to diagnose a condition, interpret your test results, or advise "
    "on medication — those need a qualified clinician. I can help you book an "
    "appointment with the right specialist, or explain what a test involves."
)


@dataclass(frozen=True)
class RedFlag:
    code: str
    priority: EscalationPriority
    reason: str


# Ordered most-severe first; detection stops escalating priority at emergency.
RED_FLAG_RULES: tuple[tuple[RedFlag, tuple[str, ...]], ...] = (
    (
        RedFlag(
            code="sudden_hearing_loss",
            priority=EscalationPriority.EMERGENCY,
            reason="Possible sudden sensorineural hearing loss — time-critical, needs same-day ENT review",
        ),
        (
            "sudden hearing loss",
            "suddenly cannot hear",
            "suddenly can't hear",
            "lost hearing suddenly",
            "woke up deaf",
            "hearing gone suddenly",
            "sudden deafness",
        ),
    ),
    (
        RedFlag(
            code="acute_trauma",
            priority=EscalationPriority.EMERGENCY,
            reason="Head or ear trauma reported — needs immediate assessment",
        ),
        (
            "head injury",
            "hit my head",
            "accident",
            "bleeding from ear",
            "blood from ear",
            "blood from my ear",
            "object stuck",
            "something stuck in ear",
            "burst eardrum",
            "ruptured eardrum",
        ),
    ),
    (
        RedFlag(
            code="neurological",
            priority=EscalationPriority.EMERGENCY,
            reason="Neurological symptoms alongside ear complaint — rule out central cause",
        ),
        (
            "facial weakness",
            "face drooping",
            "cannot move my face",
            "slurred speech",
            "double vision",
            "fainting",
            "unconscious",
            "seizure",
            "severe headache",
        ),
    ),
    (
        RedFlag(
            code="airway_swallowing",
            priority=EscalationPriority.EMERGENCY,
            reason="Possible aspiration or airway compromise — urgent dysphagia review",
        ),
        (
            "choking",
            "cannot breathe",
            "can't breathe",
            "difficulty breathing",
            "food going into lungs",
            "aspirating",
            "turning blue",
            "coughing on every feed",
        ),
    ),
    (
        RedFlag(
            code="self_harm",
            priority=EscalationPriority.EMERGENCY,
            reason="Expression of self-harm or suicidal ideation — immediate mental-health escalation",
        ),
        (
            "kill myself",
            "end my life",
            "suicide",
            "suicidal",
            "want to die",
            "harm myself",
            "hurt myself",
        ),
    ),
    (
        RedFlag(
            code="acute_infection",
            priority=EscalationPriority.URGENT,
            reason="Signs of acute ear infection — needs prompt ENT review",
        ),
        (
            "high fever",
            "pus",
            "foul smell",
            "swelling behind ear",
            "severe ear pain",
            "unbearable pain",
            "spreading redness",
        ),
    ),
    (
        RedFlag(
            code="acute_vertigo",
            priority=EscalationPriority.URGENT,
            reason="Acute vertigo with vomiting — needs prompt vestibular assessment",
        ),
        (
            "cannot stand",
            "can't stand",
            "room spinning",
            "vomiting constantly",
            "falling down",
            "keep falling",
        ),
    ),
)

# Phrases that mean "the assistant must not answer this itself".
OUT_OF_SCOPE_PATTERNS: tuple[str, ...] = (
    "what medicine",
    "which medicine",
    "which tablet",
    "what tablet",
    "prescribe",
    "prescription",
    "dosage",
    "dose of",
    "do i have",
    "is it cancer",
    "is it a tumour",
    "is it a tumor",
    "diagnose me",
    "what is my diagnosis",
    "read my report",
    "interpret my report",
    "interpret my audiogram",
    "what does my audiogram mean",
)


def detect_red_flags(text: str) -> list[RedFlag]:
    """Return every red flag whose phrasing appears in the message."""
    lowered = (text or "").lower()
    found: list[RedFlag] = []
    for flag, phrases in RED_FLAG_RULES:
        if any(p in lowered for p in phrases):
            found.append(flag)
    return found


def highest_priority(flags: Sequence[RedFlag]) -> Optional[EscalationPriority]:
    """Emergency beats urgent beats routine."""
    if not flags:
        return None
    if any(f.priority == EscalationPriority.EMERGENCY for f in flags):
        return EscalationPriority.EMERGENCY
    if any(f.priority == EscalationPriority.URGENT for f in flags):
        return EscalationPriority.URGENT
    return EscalationPriority.ROUTINE


def safety_message_for(priority: EscalationPriority) -> str:
    if priority == EscalationPriority.EMERGENCY:
        return EMERGENCY_MESSAGE
    if priority == EscalationPriority.URGENT:
        return URGENT_MESSAGE
    return OUT_OF_SCOPE_MESSAGE


def is_out_of_scope(text: str) -> bool:
    """True when the user is asking for diagnosis, medication or report reading."""
    lowered = (text or "").lower()
    return any(p in lowered for p in OUT_OF_SCOPE_PATTERNS)


@dataclass(frozen=True)
class SafetyVerdict:
    """Outcome of pre-screening a user message."""

    blocked: bool
    message: str = ""
    priority: Optional[EscalationPriority] = None
    flags: tuple[RedFlag, ...] = ()
    escalate: bool = False

    @property
    def trigger_codes(self) -> list[str]:
        return [f.code for f in self.flags]


def screen_message(text: str) -> SafetyVerdict:
    """
    Pre-flight check for every inbound assistant message.

    Red flags block the agent and raise a ticket. Out-of-scope requests block the
    agent with a redirect but do not raise a ticket, since no clinical risk is
    implied by simply asking.
    """
    flags = detect_red_flags(text)
    if flags:
        priority = highest_priority(flags) or EscalationPriority.URGENT
        return SafetyVerdict(
            blocked=True,
            message=safety_message_for(priority),
            priority=priority,
            flags=tuple(flags),
            escalate=True,
        )

    if is_out_of_scope(text):
        return SafetyVerdict(
            blocked=True,
            message=OUT_OF_SCOPE_MESSAGE,
            priority=EscalationPriority.ROUTINE,
            escalate=False,
        )

    return SafetyVerdict(blocked=False)
