"""Shared domain enums / constants for NIPMED triage."""

from __future__ import annotations

from enum import StrEnum


class UserType(StrEnum):
    MYSELF = "myself"
    MY_CHILD = "my_child"
    SOMEONE_ELSE = "someone_else"


class ConcernType(StrEnum):
    HEARING_DIFFICULTY = "hearing_difficulty"
    TINNITUS = "tinnitus"
    HYPERACUSIS = "hyperacusis"
    DIZZINESS_BALANCE = "dizziness_balance"
    EAR_PAIN_DISCHARGE = "ear_pain_discharge"
    CHILD_CONCERNS = "child_concerns"


class AgeBand(StrEnum):
    NEWBORN = "newborn"  # 0–6 months
    INFANT_TODDLER = "infant_toddler"  # 6 months–2.5 years
    PRESCHOOL = "preschool"  # 2.5–5 years
    SCHOOL_AGE = "school_age"  # 5–12 years (13+ uses adult pathway)


class SessionStep(StrEnum):
    WELCOME = "welcome"
    USER_TYPE = "user_type"
    PROFILE = "profile"
    CONCERN_SELECT = "concern_select"
    SYMPTOMS = "symptoms"
    RECOMMENDATIONS = "recommendations"
    BOOKING = "booking"
    COMPLETE = "complete"


class SessionStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class SourcePage(StrEnum):
    PAGE1 = "page1"
    PAGE2_ADULT = "page2_adult"
    PAGE3_CHILD = "page3_child"


class Vertical(StrEnum):
    """Clinical verticals of the Department of Speech, Hearing and Communication."""

    AUDIOLOGY = "audiology"
    SLP = "slp"
    EARLY_INTERVENTION = "early_intervention"
    DEPARTMENT = "department"  # cross-cutting / front-desk scope


class ClinicalDepartment(StrEnum):
    """Top-level concern group chosen at patient registration.

    Display labels (frontend):
      audiology        → Hearing and Ear related problems
      speech_language  → Speech and Speech related problems
    """

    AUDIOLOGY = "audiology"
    SPEECH_LANGUAGE = "speech_language"


class AgentType(StrEnum):
    """The five specialised departmental assistants."""

    ENQUIRY = "enquiry"
    SCHEDULING = "scheduling"
    COUNSELLING = "counselling"
    SCREENING = "screening"
    SLP_GUIDANCE = "slp_guidance"


class AppointmentStatus(StrEnum):
    REQUESTED = "requested"
    CONFIRMED = "confirmed"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


class SlotStatus(StrEnum):
    OPEN = "open"
    FULL = "full"
    BLOCKED = "blocked"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class EscalationPriority(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class EscalationStatus(StrEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    CLOSED = "closed"


class TherapyDomain(StrEnum):
    """Speech-Language Pathology practice areas."""

    ARTICULATION = "articulation"
    LANGUAGE_DELAY = "language_delay"
    FLUENCY = "fluency"
    VOICE = "voice"
    FEEDING_SWALLOWING = "feeding_swallowing"
    AUDITORY_VERBAL = "auditory_verbal"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class FlowType(StrEnum):
    """Which questionnaire pathway a patient follows."""

    ADULT = "adult"
    CHILD = "child"


class DoctorRole(StrEnum):
    """Staff roles. ADMIN is the only role permitted to edit clinical content."""

    ADMIN = "admin"
    AUDIOLOGIST = "audiologist"
    SLP = "slp"
    ENT = "ent"
    THERAPIST = "therapist"


class QuestionType(StrEnum):
    """v1 only renders single_select; the rest are reserved for later."""

    SINGLE_SELECT = "single_select"
    MULTI_SELECT = "multi_select"
    NUMERIC = "numeric"
    TEXT = "text"


class DocumentCategory(StrEnum):
    """Category of an uploaded hospital document in the RAG corpus."""

    SOP = "sop"
    GUIDELINE = "guideline"
    MANUAL = "manual"
    FAQ = "faq"
    PATIENT_EDUCATION = "patient_education"


class DocumentStatus(StrEnum):
    UPLOADED = "uploaded"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class ExplanationSource(StrEnum):
    """
    How an AI treatment explanation was produced.

    Recorded on every ai_conversations row so an auditor can tell grounded
    retrieval apart from the static fallback.
    """

    RAG = "rag"
    STATIC_FALLBACK = "static_fallback"
    CACHED = "cached"


# Staff roles allowed to manage clinical content and view audit logs.
ADMIN_ROLES: frozenset[DoctorRole] = frozenset({DoctorRole.ADMIN})

# Maps a child's age band to the flow subtype label used on patient_profiles.
CHILD_SUBTYPES: frozenset[AgeBand] = frozenset(AgeBand)


# Adult concern types shown on Page 1 selection (child_concerns routes to Page 3)
ADULT_CONCERN_TYPES: frozenset[ConcernType] = frozenset(
    {
        ConcernType.HEARING_DIFFICULTY,
        ConcernType.TINNITUS,
        ConcernType.HYPERACUSIS,
        ConcernType.DIZZINESS_BALANCE,
        ConcernType.EAR_PAIN_DISCHARGE,
    }
)

CHILD_AGE_BANDS: frozenset[AgeBand] = frozenset(AgeBand)

# Valid transitions: from_step → allowed next steps
STEP_TRANSITIONS: dict[SessionStep, frozenset[SessionStep]] = {
    SessionStep.WELCOME: frozenset({SessionStep.USER_TYPE}),
    SessionStep.USER_TYPE: frozenset({SessionStep.PROFILE}),
    SessionStep.PROFILE: frozenset({SessionStep.CONCERN_SELECT}),
    SessionStep.CONCERN_SELECT: frozenset({SessionStep.SYMPTOMS, SessionStep.CONCERN_SELECT}),
    SessionStep.SYMPTOMS: frozenset({SessionStep.SYMPTOMS, SessionStep.RECOMMENDATIONS}),
    SessionStep.RECOMMENDATIONS: frozenset({SessionStep.BOOKING, SessionStep.COMPLETE}),
    SessionStep.BOOKING: frozenset({SessionStep.COMPLETE}),
    SessionStep.COMPLETE: frozenset({SessionStep.COMPLETE}),
}

# Which clinical vertical owns each assistant. Drives escalation routing so a
# ticket lands with the team that can actually action it.
AGENT_VERTICALS: dict[AgentType, Vertical] = {
    AgentType.ENQUIRY: Vertical.DEPARTMENT,
    AgentType.SCHEDULING: Vertical.DEPARTMENT,
    AgentType.COUNSELLING: Vertical.EARLY_INTERVENTION,
    AgentType.SCREENING: Vertical.AUDIOLOGY,
    AgentType.SLP_GUIDANCE: Vertical.SLP,
}
