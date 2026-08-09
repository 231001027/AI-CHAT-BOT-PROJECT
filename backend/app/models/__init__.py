"""SQLAlchemy ORM models for NIPMED Audiology Chatbot."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(40), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    user_type: Mapped[str] = mapped_column(String(40), nullable=False)
    # Portal login id, e.g. "123/2026". Assigned at registration.
    user_code: Mapped[Optional[str]] = mapped_column(String(40), unique=True, nullable=True, index=True)
    # Also used as the patient portal password (date of birth).
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    concerns: Mapped[list[Concern]] = relationship(back_populates="patient", cascade="all, delete-orphan")
    chat_sessions: Mapped[list[ChatSession]] = relationship(back_populates="patient")


class Concern(Base):
    __tablename__ = "concerns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concern_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    source_page: Mapped[str] = mapped_column(String(40), nullable=False)
    age_band: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    patient: Mapped[Patient] = relationship(back_populates="concerns")
    symptom_responses: Mapped[list[SymptomResponse]] = relationship(
        back_populates="concern", cascade="all, delete-orphan"
    )


class SymptomResponse(Base):
    __tablename__ = "symptom_responses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    concern_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("concerns.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_key: Mapped[str] = mapped_column(String(80), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    concern: Mapped[Concern] = relationship(back_populates="symptom_responses")


class ConcernConfig(Base):
    """
    Deterministic config for concern → common_signs → recommended_tests.

    The rules engine reads ONLY from this table (+ TestCatalog). No LLM.
    """

    __tablename__ = "concern_configs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    concern_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    age_band: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    # [{ "key": "onset", "prompt": "When did it start?" }, ...]  — EDITABLE placeholders
    common_signs: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    # ["PTA", "OAE", ...] test codes referencing TestCatalog.code
    recommended_tests: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    what_it_helps: Mapped[str] = mapped_column(Text, nullable=False)
    # Optional outcome pathways for child flows
    outcome_options: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    # Optional conditional extras: [{ "when": {"question_key": "x", "answer_contains": "y"}, "add_tests": ["SPIN"] }]
    conditional_rules: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)


class TestCatalog(Base):
    __tablename__ = "test_catalog"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(60), nullable=False)  # basic | special | paediatric | vestibular
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Deterministic, admin-owned patient guidance. Kept out of the LLM's reach so
    # "how to prepare" and "how long it takes" are never hallucinated.
    preparation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    chat_history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    current_step: Mapped[str] = mapped_column(String(40), nullable=False, default="welcome")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    # Transient triage context mirrored to Redis: user_type, concern_type, age_band, active_concern_id
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    patient: Mapped[Optional[Patient]] = relationship(back_populates="chat_sessions")


class BookingRequest(Base):
    __tablename__ = "booking_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True
    )
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    preferred_slot: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---------------------------------------------------------------------------
# Departmental service catalogue and scheduling
# ---------------------------------------------------------------------------


class Service(Base):
    """A bookable departmental service (assessment, therapy session, screening camp)."""

    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    vertical: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    # Free-text preparation guidance surfaced by the enquiry + scheduling assistants
    preparation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # ["Aadhaar card", "Previous audiogram"]
    documents_required: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    report_turnaround: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    slots: Mapped[list[AppointmentSlot]] = relationship(back_populates="service")


class Clinician(Base):
    __tablename__ = "clinicians"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    designation: Mapped[str] = mapped_column(String(120), nullable=False)
    vertical: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    slots: Mapped[list[AppointmentSlot]] = relationship(back_populates="clinician")


class AppointmentSlot(Base):
    """
    A concrete bookable window. Mirrors whatever the departmental scheduling
    system exposes; `external_ref` links a row back to that system of record.
    """

    __tablename__ = "appointment_slots"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("services.id", ondelete="CASCADE"), nullable=False, index=True
    )
    clinician_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinicians.id", ondelete="SET NULL"), nullable=True, index=True
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    booked_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="open")
    location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    external_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True, index=True)

    service: Mapped[Service] = relationship(back_populates="slots")
    clinician: Mapped[Optional[Clinician]] = relationship(back_populates="slots")
    appointments: Mapped[list[Appointment]] = relationship(back_populates="slot")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    reference_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    slot_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("appointment_slots.id", ondelete="SET NULL"), nullable=True, index=True
    )
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True
    )
    patient_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="requested", index=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_ref: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    # Direct doctor assignment for appointments raised from the clinical flow
    # rather than by picking a slot. Slot-based bookings leave these null and
    # derive the clinician and time from the slot.
    doctor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True, index=True
    )
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    slot: Mapped[Optional[AppointmentSlot]] = relationship(back_populates="appointments")


# ---------------------------------------------------------------------------
# Clinical flow: profiles, staff, question bank, rules, plans, reports
# ---------------------------------------------------------------------------


class PatientProfile(Base):
    """Which pathway a patient was routed down, captured at registration."""

    __tablename__ = "patient_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    flow_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # audiology | speech_language — chosen at registration
    department: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    # Only set for the child flow; mirrors AgeBand
    child_subtype: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    # Guardian consent is required before a child's data is processed
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    consent_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class Doctor(Base):
    """Departmental staff account. The only entity that authenticates."""

    __tablename__ = "doctors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False, index=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    role: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class TreatmentCategory(Base):
    """Top-level 'what can I help you with?' grouping, editable by admins."""

    __tablename__ = "treatment_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    flow_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # audiology | speech_language
    department: Mapped[str] = mapped_column(
        String(40), nullable=False, default="audiology", index=True
    )
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    conditions: Mapped[list[Condition]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class Condition(Base):
    """A specific presentation within a category, owning a question set."""

    __tablename__ = "conditions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("treatment_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slug: Mapped[str] = mapped_column(String(80), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    category: Mapped[TreatmentCategory] = relationship(back_populates="conditions")
    questions: Mapped[list[Question]] = relationship(
        back_populates="condition", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    condition_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conditions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Stable key the rule engine references, so reordering questions or editing
    # their wording never silently changes which rules fire.
    key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    help_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    question_type: Mapped[str] = mapped_column(String(30), nullable=False, default="single_select")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # True for the first question of a condition's flow
    is_entry: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    condition: Mapped[Condition] = relationship(back_populates="questions")
    options: Mapped[list[QuestionOption]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        foreign_keys="QuestionOption.question_id",
    )


class QuestionOption(Base):
    """
    One selectable answer.

    ``next_question_id`` gives per-option branching: a 'Not sure' answer can lead
    somewhere different from 'Left ear'. Null means fall through to the next
    question by display_order.
    """

    __tablename__ = "question_options"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    label: Mapped[str] = mapped_column(String(300), nullable=False)
    # Machine value the rule engine compares against
    value: Mapped[str] = mapped_column(String(80), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    next_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    # When true, selecting this option ends the questionnaire immediately
    is_terminal: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    question: Mapped[Question] = relationship(
        back_populates="options", foreign_keys=[question_id]
    )


class QuestionnaireSession(Base):
    """One pass through a condition's questions by one patient."""

    __tablename__ = "questionnaire_sessions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("treatment_categories.id", ondelete="SET NULL"), nullable=True
    )
    condition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conditions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active", index=True)
    current_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    answers: Mapped[list[PatientAnswer]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class PatientAnswer(Base):
    __tablename__ = "patient_answers"
    __table_args__ = (
        # One answer per question per pass; re-answering updates in place.
        UniqueConstraint("session_id", "question_id", name="uq_patient_answer_session_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("questions.id", ondelete="CASCADE"), nullable=False
    )
    selected_option_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("question_options.id", ondelete="SET NULL"), nullable=True
    )
    # Denormalised so a later edit to the question bank cannot rewrite history
    question_key: Mapped[str] = mapped_column(String(80), nullable=False)
    answer_value: Mapped[str] = mapped_column(String(200), nullable=False)
    answer_label: Mapped[str] = mapped_column(Text, nullable=False, default="")
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    session: Mapped[QuestionnaireSession] = relationship(back_populates="answers")


class ClinicalRule(Base):
    """
    An admin-authored predicate over questionnaire answers and patient facts.

    ``rule_definition`` holds a structured boolean tree evaluated by
    services/clinical_rules.py. No LLM is ever consulted.
    """

    __tablename__ = "clinical_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("treatment_categories.id", ondelete="CASCADE"), nullable=True
    )
    condition_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conditions.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # {"all": [{"field": "sudden", "op": "eq", "value": "yes"}]}
    rule_definition: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # Higher runs first; also orders the resulting test list
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # When true this rule's tests are always included for the condition
    is_baseline: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    tests: Mapped[list[RuleRecommendedTest]] = relationship(
        back_populates="rule", cascade="all, delete-orphan"
    )


class RuleRecommendedTest(Base):
    """A test a rule recommends, with the reason shown to the patient."""

    __tablename__ = "recommended_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clinical_rules.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # References TestCatalog.code but not enforced, so admins can stage a test
    # before it exists in the catalogue
    test_code: Mapped[str] = mapped_column(String(60), nullable=False)
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    reason_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    display_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    rule: Mapped[ClinicalRule] = relationship(back_populates="tests")


class TreatmentPlan(Base):
    """
    Immutable snapshot of what the rule engine produced for one session.

    Snapshotted rather than recomputed so a report issued today still reflects
    the rules that were in force when it was generated.
    """

    __tablename__ = "treatment_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # [{"test_code", "test_name", "reason_text", "rule_name"}]
    recommended_tests: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list
    )
    matched_rule_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    general_recommendations: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    plan_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("treatment_plans.id", ondelete="SET NULL"), nullable=True
    )
    # Full structured content the PDF was rendered from, so the exact document
    # can be reproduced from the database alone
    report_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    pdf_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class AiConversation(Base):
    """
    Audit record for one RAG treatment explanation.

    ``prompt_context`` stores the retrieved chunks verbatim so a reviewer can
    confirm the explanation was grounded in departmental documents.
    """

    __tablename__ = "ai_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True, index=True
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questionnaire_sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    recommended_test_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # [{"document_id", "title", "chunk_index", "text", "score"}]
    prompt_context: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, default=list)
    response_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(30), nullable=False, default="rag", index=True)
    model: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class HospitalDocument(Base):
    """An uploaded departmental document backing the RAG corpus."""

    __tablename__ = "hospital_documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # Test codes this document explains, used to bias retrieval
    test_tags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="uploaded", index=True)
    vector_indexed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    index_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


class StaticExplanation(Base):
    """
    Admin-authored fallback explanation per test.

    Used when retrieval finds nothing relevant or the LLM is unavailable, so the
    patient still gets approved wording instead of an ungrounded answer.
    """

    __tablename__ = "static_explanations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    test_code: Mapped[str] = mapped_column(String(60), unique=True, nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


# ---------------------------------------------------------------------------
# Curated departmental knowledge — the only source the assistants may quote
# ---------------------------------------------------------------------------


class KnowledgeEntry(Base):
    """
    Clinician-authored Q&A used by the enquiry/screening/SLP assistants.

    Retrieval is deterministic keyword scoring (see services/knowledge_base.py).
    The LLM may only rephrase what retrieval returns — it never invents content.
    """

    __tablename__ = "knowledge_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    vertical: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    # Which assistants may surface this entry; empty list = all
    agent_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    # Bumps ranking for entries the department wants surfaced first
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )


class ScreeningProtocol(Base):
    """Hearing screening pathway per age band — owned by Audiology."""

    __tablename__ = "screening_protocols"
    __table_args__ = (UniqueConstraint("age_band", name="uq_screening_protocol_age_band"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    age_band: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    test_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    # ["Refer if no OAE response in either ear", ...]
    referral_criteria: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    timeline: Mapped[str] = mapped_column(Text, nullable=False)
    preparation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class TherapyGuideline(Base):
    """Speech-Language Pathology guidance per domain + age band."""

    __tablename__ = "therapy_guidelines"
    __table_args__ = (
        UniqueConstraint("domain", "age_band", name="uq_therapy_guideline_domain_age"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    domain: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    age_band: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    milestones: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    home_activities: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    red_flags: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    typical_frequency: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)


class CounsellingResource(Base):
    """Parent counselling talking points — owned by Early Intervention."""

    __tablename__ = "counselling_resources"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    age_band: Mapped[Optional[str]] = mapped_column(String(40), nullable=True, index=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    talking_points: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    reassurance: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    next_steps: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    keywords: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)


# ---------------------------------------------------------------------------
# Agent conversations, transcripts and human hand-off
# ---------------------------------------------------------------------------


class AgentConversation(Base):
    __tablename__ = "agent_conversations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    agent_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    vertical: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True, index=True
    )
    patient_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="active", index=True)
    # Assistant-specific working memory (e.g. scheduling draft, chosen service)
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow
    )

    messages: Mapped[list[AgentMessage]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )


class AgentMessage(Base):
    """One turn of an agent conversation, including tool calls for auditability."""

    __tablename__ = "agent_messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # [{"tool": "find_available_slots", "input": {...}, "output": {...}}]
    tool_calls: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSONB, nullable=True)
    # Which knowledge entries / protocol rows backed this answer
    sources: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    conversation: Mapped[AgentConversation] = relationship(back_populates="messages")


class EscalationTicket(Base):
    """Raised when an assistant must hand off to a human clinician."""

    __tablename__ = "escalation_tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=_uuid)
    reference_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    conversation_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True
    )
    agent_type: Mapped[str] = mapped_column(String(40), nullable=False)
    vertical: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="routine", index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open", index=True)
    contact_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # Red-flag codes that triggered an automatic escalation
    triggers: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
