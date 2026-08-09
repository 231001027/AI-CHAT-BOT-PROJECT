"""Session lifecycle routes: start, user-type, profile."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis_client import cache_session_state
from app.db.session import get_db
from app.models import ChatSession, Patient
from app.models.enums import SessionStatus, SessionStep, UserType
from app.schemas import (
    ProfileRequest,
    ProfileResponse,
    SessionStartResponse,
    UserTypeRequest,
    UserTypeResponse,
)
from app.services import state_machine as sm

router = APIRouter(prefix="/api/session", tags=["Session"])


async def _get_session(db: AsyncSession, session_id: UUID) -> ChatSession:
    row = await db.get(ChatSession, session_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if row.status != SessionStatus.ACTIVE.value:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Session is not active")
    return row


async def _sync_redis(session: ChatSession) -> None:
    await cache_session_state(
        str(session.id),
        {
            "current_step": session.current_step,
            "status": session.status,
            "patient_id": str(session.patient_id) if session.patient_id else None,
            "context": session.context or {},
        },
    )


@router.post("/start", response_model=SessionStartResponse)
async def start_session(db: AsyncSession = Depends(get_db)):
    session = ChatSession(
        current_step=SessionStep.WELCOME.value,
        status=SessionStatus.ACTIVE.value,
        chat_history=[],
        context={},
    )
    db.add(session)
    await db.flush()
    # Move immediately to user_type (welcome is shown by start response)
    session.current_step = SessionStep.USER_TYPE.value
    await db.flush()
    await _sync_redis(session)
    return SessionStartResponse(
        session_id=session.id,
        current_step=SessionStep.USER_TYPE,
        status=SessionStatus.ACTIVE,
    )


@router.post("/user-type", response_model=UserTypeResponse)
async def set_user_type(body: UserTypeRequest, db: AsyncSession = Depends(get_db)):
    session = await _get_session(db, body.session_id)
    current = sm.parse_step(session.current_step)
    sm.assert_step(current, {SessionStep.USER_TYPE, SessionStep.WELCOME}, "set_user_type")

    ctx = dict(session.context or {})
    ctx["user_type"] = body.user_type.value
    session.context = ctx
    session.current_step = sm.transition(current, SessionStep.PROFILE).value
    await db.flush()
    await _sync_redis(session)

    labels = {
        UserType.MYSELF: "yourself",
        UserType.MY_CHILD: "your child",
        UserType.SOMEONE_ELSE: "someone else",
    }
    return UserTypeResponse(
        session_id=session.id,
        user_type=body.user_type,
        current_step=SessionStep.PROFILE,
        next_step=SessionStep.PROFILE,
        message=f"Thanks — we'll continue the assessment for {labels[body.user_type]}. Please share basic details.",
    )


@router.post("/profile", response_model=ProfileResponse)
async def save_profile(body: ProfileRequest, db: AsyncSession = Depends(get_db)):
    session = await _get_session(db, body.session_id)
    current = sm.parse_step(session.current_step)
    sm.assert_step(current, {SessionStep.PROFILE}, "save_profile")

    ctx = dict(session.context or {})
    user_type_raw = ctx.get("user_type")
    if not user_type_raw:
        raise HTTPException(status_code=400, detail="user_type must be set before profile")
    user_type = UserType(user_type_raw)

    patient = Patient(
        name=body.name,
        district=body.district,
        age=body.age,
        gender=body.gender,
        phone=body.phone,
        user_type=user_type.value,
    )
    db.add(patient)
    await db.flush()

    session.patient_id = patient.id
    route = sm.route_hint_for_profile(user_type, body.age)
    ctx["route_hint"] = route
    if route == "child":
        band = sm.age_band_for_age(float(body.age))
        if band:
            ctx["suggested_age_band"] = band.value
    session.context = ctx
    session.current_step = sm.transition(current, SessionStep.CONCERN_SELECT).value
    await db.flush()
    await _sync_redis(session)

    return ProfileResponse(
        session_id=session.id,
        patient_id=patient.id,
        current_step=SessionStep.CONCERN_SELECT,
        next_step=SessionStep.CONCERN_SELECT,
        route_hint=route,
        message=(
            "Profile saved. Please select a concern category, or describe the problem in your own words."
        ),
    )


@router.get("/{session_id}")
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    session = await db.get(ChatSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session.id,
        "patient_id": session.patient_id,
        "current_step": session.current_step,
        "status": session.status,
        "context": session.context,
        "chat_history": session.chat_history,
    }
