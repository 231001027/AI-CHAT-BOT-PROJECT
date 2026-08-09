"""Pydantic request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.models.enums import AgeBand, ConcernType, SessionStep, SessionStatus, UserType


# ── Session ───────────────────────────────────────────────────────────────────

class SessionStartResponse(BaseModel):
    session_id: UUID
    current_step: SessionStep
    status: SessionStatus
    message: str = "Welcome to NIPMED Audiology. Who is this assessment for?"


class UserTypeRequest(BaseModel):
    session_id: UUID
    user_type: UserType


class UserTypeResponse(BaseModel):
    session_id: UUID
    user_type: UserType
    current_step: SessionStep
    next_step: SessionStep
    message: str


class ProfileRequest(BaseModel):
    session_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    district: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., min_length=1, max_length=40)
    phone: Optional[str] = Field(None, max_length=30)


class ProfileResponse(BaseModel):
    session_id: UUID
    patient_id: UUID
    current_step: SessionStep
    next_step: SessionStep
    route_hint: str  # "adult" | "child" based on age / user_type
    message: str


# ── Chat / intent ─────────────────────────────────────────────────────────────

class ChatMessageRequest(BaseModel):
    session_id: UUID
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    session_id: UUID
    concern_type: Optional[ConcernType] = None
    confidence: float = 0.0
    reply: str
    current_step: SessionStep
    suggested_age_band: Optional[AgeBand] = None


# ── Concerns ──────────────────────────────────────────────────────────────────

class CommonSignOut(BaseModel):
    key: str
    prompt: str


class ConcernConfigOut(BaseModel):
    concern_type: ConcernType
    age_band: Optional[AgeBand] = None
    common_signs: list[CommonSignOut]
    recommended_tests: list[str]
    what_it_helps: str
    outcome_options: Optional[list[str]] = None


class SelectConcernRequest(BaseModel):
    session_id: UUID
    concern_type: ConcernType
    age_band: Optional[AgeBand] = None


class SelectConcernResponse(BaseModel):
    session_id: UUID
    concern_id: UUID
    concern_type: ConcernType
    age_band: Optional[AgeBand] = None
    source_page: str
    current_step: SessionStep
    config: ConcernConfigOut


# ── Symptoms ──────────────────────────────────────────────────────────────────

class SymptomAnswerRequest(BaseModel):
    session_id: UUID
    concern_id: UUID
    question_key: str = Field(..., min_length=1, max_length=80)
    answer: str = Field(..., min_length=1, max_length=2000)


class SymptomAnswerResponse(BaseModel):
    id: UUID
    concern_id: UUID
    question_key: str
    answer: str
    answers_so_far: int
    current_step: SessionStep


# ── Tests ─────────────────────────────────────────────────────────────────────

class RecommendedTestOut(BaseModel):
    code: str
    name: str
    category: str
    description: str
    reason: str = "Configured for this concern pathway"


class RecommendTestsResponse(BaseModel):
    concern_id: UUID
    concern_type: ConcernType
    age_band: Optional[AgeBand] = None
    tests: list[RecommendedTestOut]
    what_it_helps: str
    outcome_options: Optional[list[str]] = None
    general_recommendations: list[str]


class TestDetailOut(BaseModel):
    code: str
    name: str
    category: str
    description: str


# ── Booking ───────────────────────────────────────────────────────────────────

class BookingRequestIn(BaseModel):
    session_id: Optional[UUID] = None
    name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=5, max_length=30)
    email: Optional[EmailStr] = None
    preferred_slot: Optional[str] = Field(None, max_length=120)
    notes: Optional[str] = Field(None, max_length=2000)


class BookingResponse(BaseModel):
    id: UUID
    status: str = "received"
    message: str
    created_at: datetime


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
