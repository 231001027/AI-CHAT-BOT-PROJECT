"""Request/response models for the clinical flow, reports and admin screens."""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.enums import (
    AgeBand,
    ClinicalDepartment,
    DocumentCategory,
    DoctorRole,
    FlowType,
    QuestionType,
    UserType,
)

# Shown on every AI-generated surface, including the report PDF.
SAFETY_DISCLAIMER = (
    "This information is for education only. It is not a diagnosis and not a "
    "prescription. Only a qualified audiologist or doctor can diagnose a condition "
    "after examining you and reviewing your test results."
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class DoctorOut(ORMModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    role: DoctorRole
    specialization: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    doctor: DoctorOut


class RefreshRequest(BaseModel):
    refresh_token: str


class DoctorCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=200)
    role: DoctorRole = DoctorRole.AUDIOLOGIST
    specialization: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)


class DoctorUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    password: Optional[str] = Field(default=None, min_length=8, max_length=200)
    role: Optional[DoctorRole] = None
    specialization: Optional[str] = Field(default=None, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)
    is_active: Optional[bool] = None


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------


class PatientRegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=40)
    district: str = Field(min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)
    # Maps to patients.user_type: myself | my_child | someone_else
    relationship: UserType = UserType.MYSELF
    flow_type: Optional[FlowType] = None
    child_subtype: Optional[AgeBand] = None
    department: ClinicalDepartment = ClinicalDepartment.AUDIOLOGY
    # Used as the patient portal password and for age verification.
    date_of_birth: date
    # Required before any child's data is processed
    consent_given: bool = False
    consent_by: Optional[str] = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def _normalise_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        digits = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        return digits or None

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


class PatientUpdateRequest(BaseModel):
    """Complete or refresh registration details for an existing patient account."""

    name: str = Field(min_length=2, max_length=200)
    age: int = Field(ge=0, le=120)
    gender: str = Field(min_length=1, max_length=40)
    district: str = Field(min_length=2, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)
    relationship: UserType = UserType.MYSELF
    flow_type: Optional[FlowType] = None
    child_subtype: Optional[AgeBand] = None
    department: ClinicalDepartment = ClinicalDepartment.AUDIOLOGY
    date_of_birth: date
    consent_given: bool = False
    consent_by: Optional[str] = Field(default=None, max_length=200)

    @field_validator("phone")
    @classmethod
    def _normalise_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        digits = "".join(ch for ch in value if ch.isdigit() or ch == "+")
        return digits or None

    @field_validator("date_of_birth")
    @classmethod
    def _dob_not_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Date of birth cannot be in the future.")
        return value


class PatientLoginRequest(BaseModel):
    """Patient portal login: User ID + date of birth as password."""

    user_id: str = Field(min_length=3, max_length=40, description="e.g. 123/2026")
    password: str = Field(
        min_length=8,
        max_length=32,
        description="Date of birth as YYYY-MM-DD, DD/MM/YYYY, or DD-MM-YYYY",
    )


class PatientSignupRequest(BaseModel):
    """Sign up after relationship selection: User ID + date of birth."""

    user_id: Optional[str] = Field(
        default=None,
        max_length=40,
        description="Optional. e.g. 123/2026 — leave empty to auto-assign",
    )
    password: str = Field(
        min_length=8,
        max_length=32,
        description="Date of birth as YYYY-MM-DD",
    )
    relationship: UserType = UserType.MYSELF
    department: ClinicalDepartment = ClinicalDepartment.AUDIOLOGY
    consent_given: bool = False
    consent_by: Optional[str] = Field(default=None, max_length=200)

    @field_validator("user_id")
    @classmethod
    def _normalise_user_id(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        text = value.strip()
        if not text:
            return None
        if not re.fullmatch(r"\d+/\d{4}", text):
            raise ValueError("User ID must look like 123/2026")
        return text


class PatientProfileOut(ORMModel):
    id: uuid.UUID
    flow_type: FlowType
    department: Optional[ClinicalDepartment] = None
    child_subtype: Optional[AgeBand] = None
    consent_given: bool
    consent_by: Optional[str] = None
    consent_at: Optional[datetime] = None


class PatientOut(ORMModel):
    id: uuid.UUID
    name: str
    age: int
    gender: str
    district: str
    phone: Optional[str] = None
    user_type: UserType
    user_code: Optional[str] = None
    date_of_birth: Optional[date] = None
    created_at: datetime
    profile: Optional[PatientProfileOut] = None


class PatientListResponse(BaseModel):
    total: int
    items: list[PatientOut]


# ---------------------------------------------------------------------------
# Categories, conditions, question bank
# ---------------------------------------------------------------------------


class CategoryOut(ORMModel):
    id: uuid.UUID
    slug: str
    name: str
    flow_type: FlowType
    department: ClinicalDepartment = ClinicalDepartment.AUDIOLOGY
    description: str
    display_order: int


class ConditionOut(ORMModel):
    id: uuid.UUID
    category_id: uuid.UUID
    slug: str
    name: str
    description: str
    display_order: int


class OptionOut(ORMModel):
    id: uuid.UUID
    label: str
    value: str
    display_order: int
    next_question_id: Optional[uuid.UUID] = None
    is_terminal: bool


class QuestionOut(ORMModel):
    id: uuid.UUID
    condition_id: uuid.UUID
    key: str
    text: str
    help_text: Optional[str] = None
    display_order: int
    question_type: QuestionType
    is_entry: bool
    options: list[OptionOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Questionnaire sessions
# ---------------------------------------------------------------------------


class SessionStartRequest(BaseModel):
    patient_id: uuid.UUID
    condition_id: uuid.UUID


class ProgressOut(BaseModel):
    answered: int
    total: int


class SessionStateOut(BaseModel):
    session_id: uuid.UUID
    patient_id: uuid.UUID
    condition_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    status: str
    is_complete: bool
    question: Optional[QuestionOut] = None
    progress: ProgressOut


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    option_id: uuid.UUID


class AnswerOut(ORMModel):
    question_id: uuid.UUID
    question_key: str
    question_text: str = ""
    answer_value: str
    answer_label: str
    answered_at: datetime


class SessionSummaryOut(BaseModel):
    session_id: uuid.UUID
    patient: PatientOut
    category: Optional[CategoryOut] = None
    condition: Optional[ConditionOut] = None
    status: str
    answers: list[AnswerOut]
    created_at: datetime
    completed_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Recommendations
# ---------------------------------------------------------------------------


class EvaluateRequest(BaseModel):
    session_id: uuid.UUID


class RecommendedTestOut(BaseModel):
    test_code: str
    test_name: str
    reason_text: str
    rule_name: str
    # Populated from TestCatalog where a matching code exists
    description: Optional[str] = None
    preparation: Optional[str] = None
    duration_minutes: Optional[int] = None


class RecommendationOut(BaseModel):
    session_id: uuid.UUID
    plan_id: uuid.UUID
    recommended_tests: list[RecommendedTestOut]
    general_recommendations: list[str]
    matched_rule_ids: list[uuid.UUID] = Field(default_factory=list)
    generated_at: datetime
    disclaimer: str = SAFETY_DISCLAIMER


# ---------------------------------------------------------------------------
# AI treatment assistant (RAG)
# ---------------------------------------------------------------------------


class ExplainTestRequest(BaseModel):
    test_name: str = Field(min_length=1, max_length=200)
    test_code: Optional[str] = Field(default=None, max_length=60)
    session_id: Optional[uuid.UUID] = None
    patient_id: Optional[uuid.UUID] = None
    question: Optional[str] = Field(default=None, max_length=500)


class SourceChunkOut(BaseModel):
    document_id: Optional[uuid.UUID] = None
    title: str
    chunk_index: int
    score: float
    excerpt: str


class ExplanationOut(BaseModel):
    test_name: str
    explanation: str
    # "rag" | "static_fallback" | "cached" — lets the UI and auditors tell a
    # grounded answer apart from the approved fallback text.
    source: str
    sources: list[SourceChunkOut] = Field(default_factory=list)
    model: Optional[str] = None
    disclaimer: str = SAFETY_DISCLAIMER


class AiConversationOut(ORMModel):
    id: uuid.UUID
    patient_id: Optional[uuid.UUID] = None
    session_id: Optional[uuid.UUID] = None
    recommended_test_name: str
    question: Optional[str] = None
    response_text: str
    source: str
    model: Optional[str] = None
    prompt_context: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class GenerateReportRequest(BaseModel):
    session_id: uuid.UUID
    # Include the RAG explanations already generated for this session
    include_explanations: bool = True


class ReportOut(ORMModel):
    id: uuid.UUID
    patient_id: uuid.UUID
    session_id: uuid.UUID
    generated_at: datetime
    download_url: str = ""
    report_json: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Admin: question bank and rules
# ---------------------------------------------------------------------------


class CategoryCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    flow_type: FlowType
    department: ClinicalDepartment = ClinicalDepartment.AUDIOLOGY
    description: str = ""
    display_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    flow_type: Optional[FlowType] = None
    department: Optional[ClinicalDepartment] = None
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class ConditionCreate(BaseModel):
    category_id: uuid.UUID
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
    display_order: int = 0


class ConditionUpdate(BaseModel):
    category_id: Optional[uuid.UUID] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class QuestionCreate(BaseModel):
    condition_id: uuid.UUID
    key: str = Field(min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")
    text: str = Field(min_length=3)
    help_text: Optional[str] = None
    display_order: int = 0
    question_type: QuestionType = QuestionType.SINGLE_SELECT
    is_entry: bool = False


class QuestionUpdate(BaseModel):
    key: Optional[str] = Field(default=None, min_length=2, max_length=80, pattern=r"^[a-z0-9_]+$")
    text: Optional[str] = Field(default=None, min_length=3)
    help_text: Optional[str] = None
    display_order: Optional[int] = None
    question_type: Optional[QuestionType] = None
    is_entry: Optional[bool] = None
    is_active: Optional[bool] = None


class OptionCreate(BaseModel):
    question_id: uuid.UUID
    label: str = Field(min_length=1, max_length=300)
    value: str = Field(min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    display_order: int = 0
    next_question_id: Optional[uuid.UUID] = None
    is_terminal: bool = False


class OptionUpdate(BaseModel):
    label: Optional[str] = Field(default=None, min_length=1, max_length=300)
    value: Optional[str] = Field(default=None, min_length=1, max_length=80, pattern=r"^[a-z0-9_]+$")
    display_order: Optional[int] = None
    next_question_id: Optional[uuid.UUID] = None
    is_terminal: Optional[bool] = None


class RuleTestIn(BaseModel):
    test_code: str = Field(min_length=1, max_length=60)
    test_name: str = Field(min_length=1, max_length=200)
    reason_text: str = ""
    display_order: int = 0


class RuleCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str = ""
    category_id: Optional[uuid.UUID] = None
    condition_id: Optional[uuid.UUID] = None
    rule_definition: dict[str, Any] = Field(default_factory=dict)
    priority: int = 0
    is_baseline: bool = False
    tests: list[RuleTestIn] = Field(default_factory=list)


class RuleUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    condition_id: Optional[uuid.UUID] = None
    rule_definition: Optional[dict[str, Any]] = None
    priority: Optional[int] = None
    is_baseline: Optional[bool] = None
    is_active: Optional[bool] = None
    tests: Optional[list[RuleTestIn]] = None


class RuleTestOut(ORMModel):
    id: uuid.UUID
    test_code: str
    test_name: str
    reason_text: str
    display_order: int


class RuleOut(ORMModel):
    id: uuid.UUID
    name: str
    description: str
    category_id: Optional[uuid.UUID] = None
    condition_id: Optional[uuid.UUID] = None
    rule_definition: dict[str, Any]
    priority: int
    is_baseline: bool
    is_active: bool
    tests: list[RuleTestOut] = Field(default_factory=list)


class RuleValidateRequest(BaseModel):
    rule_definition: dict[str, Any]
    # Sample facts to dry-run the rule against before saving
    sample_facts: dict[str, Any] = Field(default_factory=dict)


class RuleValidateResponse(BaseModel):
    is_valid: bool
    matches_sample: Optional[bool] = None
    error: Optional[str] = None
    referenced_fields: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Admin: documents and dashboard
# ---------------------------------------------------------------------------


class DocumentOut(ORMModel):
    id: uuid.UUID
    title: str
    category: DocumentCategory
    original_filename: Optional[str] = None
    size_bytes: Optional[int] = None
    test_tags: list[str] = Field(default_factory=list)
    status: str
    vector_indexed: bool
    chunk_count: int
    index_error: Optional[str] = None
    uploaded_at: datetime


class DocumentListResponse(BaseModel):
    total: int
    items: list[DocumentOut]
    # False when no embedding backend or Qdrant is reachable; the UI warns that
    # uploads will be stored but not searchable yet.
    indexing_available: bool = True


class StaticExplanationIn(BaseModel):
    test_code: str = Field(min_length=1, max_length=60)
    test_name: str = Field(min_length=1, max_length=200)
    explanation: str = Field(min_length=10)


class StaticExplanationOut(ORMModel):
    id: uuid.UUID
    test_code: str
    test_name: str
    explanation: str
    updated_at: datetime


class DashboardStats(BaseModel):
    patients_total: int
    patients_last_7_days: int
    sessions_total: int
    sessions_completed: int
    plans_generated: int
    reports_generated: int
    ai_explanations: int
    ai_fallback_rate: float
    documents_indexed: int
    documents_total: int
    appointments_upcoming: int
    escalations_open: int
    rules_active: int
    questions_active: int
