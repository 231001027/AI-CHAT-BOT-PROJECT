"""Request/response schemas for the assistant suite, scheduling and guidance."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import (
    AgeBand,
    AgentType,
    EscalationPriority,
    TherapyDomain,
    Vertical,
)

# ---------------------------------------------------------------------------
# Assistants
# ---------------------------------------------------------------------------


class AgentSummary(BaseModel):
    id: str
    name: str
    vertical: Vertical
    tagline: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    sample_prompts: list[str] = Field(default_factory=list)


class ToolCallOut(BaseModel):
    tool: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)


class AgentChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None


class AgentChatResponse(BaseModel):
    conversation_id: UUID
    agent_id: str
    agent_name: str
    vertical: Vertical
    reply: str
    tool_calls: list[ToolCallOut] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    escalated: bool = False
    escalation_reference: Optional[str] = None
    escalation_priority: Optional[EscalationPriority] = None
    used_fallback: bool = False
    # Present when the supervisor picked the assistant rather than the caller
    routed: bool = False
    routing_confidence: Optional[float] = None


class RouteRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)


class RouteResponse(BaseModel):
    agent_id: str
    agent_name: str
    vertical: Vertical
    confidence: float
    method: str
    rationale: str = ""


class AgentMessageOut(BaseModel):
    role: str
    content: str
    tool_calls: Optional[list[dict[str, Any]]] = None
    sources: Optional[list[str]] = None
    created_at: datetime


class ConversationOut(BaseModel):
    id: UUID
    agent_id: str
    vertical: Vertical
    status: str
    context: dict[str, Any] = Field(default_factory=dict)
    messages: list[AgentMessageOut] = Field(default_factory=list)
    created_at: datetime


class EscalationRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=2000)
    agent_id: Optional[str] = None
    conversation_id: Optional[UUID] = None
    priority: EscalationPriority = EscalationPriority.ROUTINE
    contact_name: Optional[str] = Field(default=None, max_length=200)
    contact_phone: Optional[str] = Field(default=None, max_length=30)


class EscalationResponse(BaseModel):
    reference_code: str
    priority: EscalationPriority
    status: str
    message: str


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------


class ServiceOut(BaseModel):
    code: str
    name: str
    vertical: Vertical
    duration_minutes: int
    description: str
    preparation: Optional[str] = None
    documents_required: list[str] = Field(default_factory=list)
    report_turnaround: Optional[str] = None


class SlotOut(BaseModel):
    slot_id: str
    service_code: str
    service_name: str
    starts_at: datetime
    ends_at: datetime
    seats_left: int
    clinician_name: Optional[str] = None
    location: Optional[str] = None
    human_readable: str


class CreateAppointmentRequest(BaseModel):
    slot_id: str
    patient_name: str = Field(min_length=1, max_length=200)
    phone: str = Field(min_length=5, max_length=30)
    email: Optional[EmailStr] = None
    notes: Optional[str] = Field(default=None, max_length=2000)
    conversation_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None


class RescheduleRequest(BaseModel):
    new_slot_id: str


class AppointmentOut(BaseModel):
    reference_code: str
    status: str
    service_name: str
    starts_at: Optional[datetime] = None
    patient_name: str
    phone: str
    clinician_name: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Knowledge and guidance
# ---------------------------------------------------------------------------


class KnowledgeHitOut(BaseModel):
    slug: str
    topic: str
    question: str
    answer: str
    vertical: Vertical
    score: float


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[KnowledgeHitOut] = Field(default_factory=list)


class ScreeningProtocolOut(BaseModel):
    age_band: AgeBand
    name: str
    summary: str
    test_codes: list[str] = Field(default_factory=list)
    referral_criteria: list[str] = Field(default_factory=list)
    timeline: str
    preparation: Optional[str] = None


class TherapyGuidelineOut(BaseModel):
    domain: TherapyDomain
    age_band: Optional[AgeBand] = None
    title: str
    summary: str
    milestones: list[str] = Field(default_factory=list)
    home_activities: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    typical_frequency: Optional[str] = None


class CounsellingResourceOut(BaseModel):
    slug: str
    topic: str
    age_band: Optional[AgeBand] = None
    summary: str
    talking_points: list[str] = Field(default_factory=list)
    reassurance: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
