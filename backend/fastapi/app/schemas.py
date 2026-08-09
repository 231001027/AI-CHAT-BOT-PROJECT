"""Pydantic request/response schemas for the HearConnect API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message text")


class ChatResponse(BaseModel):
    response: str
    followups: list[str]
    matched_keywords: list[str]


# ── Domain data ───────────────────────────────────────────────────────────────

class HearingProblem(BaseModel):
    id: str
    title: str
    accent: str
    symptoms: list[str]
    route: str


class AdultSection(BaseModel):
    id: str
    title: str
    accent: str
    questions: list[str]
    tests: list[str]


class SpecialTest(BaseModel):
    code: str
    name: str
    description: str


class ChildCategory(BaseModel):
    id: str
    title: str
    ageRange: str
    accent: str
    questions: list[str]
    tests: list[str]


# ── Assessments ───────────────────────────────────────────────────────────────

class AssessmentCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    district: str = Field(..., min_length=1, max_length=120)
    age: int = Field(..., ge=0, le=120)
    gender: str = Field(..., min_length=1, max_length=40)
    phone: Optional[str] = Field(None, max_length=30)
    audience: Optional[str] = Field(None, max_length=40)
    routed_to: Optional[str] = Field(None, max_length=40)


class AssessmentOut(AssessmentCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chat sessions / messages ──────────────────────────────────────────────────

class ChatSessionCreate(BaseModel):
    topic_id: str = Field(..., min_length=1, max_length=80)
    topic_title: str = Field(..., min_length=1, max_length=200)


class ChatSessionOut(ChatSessionCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=36)
    role: Literal["bot", "user"]
    message: str = Field(..., min_length=1, max_length=5000)
    question_index: Optional[int] = Field(None, ge=0)


class ChatMessageBulkCreate(BaseModel):
    messages: list[ChatMessageCreate] = Field(..., min_length=1)


class ChatMessageOut(ChatMessageCreate):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Contact ───────────────────────────────────────────────────────────────────

class ContactCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: EmailStr
    subject: Optional[str] = Field(None, max_length=200)
    message: str = Field(..., min_length=1, max_length=5000)


class ContactOut(BaseModel):
    id: str
    created_at: datetime
    status: str = "received"


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
