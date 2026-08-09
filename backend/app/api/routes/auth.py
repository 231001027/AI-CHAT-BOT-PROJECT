"""Staff authentication. Patients do not have accounts."""

from __future__ import annotations

import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentDoctor
from app.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    verify_password,
)
from app.db.session import get_db
from app.models import Doctor
from app.schemas.clinical import DoctorOut, LoginRequest, RefreshRequest, TokenResponse

logger = logging.getLogger("nipmed.auth")

router = APIRouter(prefix="/api/auth", tags=["auth"])

INVALID_CREDENTIALS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect email or password.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _tokens_for(doctor: Doctor) -> TokenResponse:
    settings = get_settings()
    claims = {"role": doctor.role, "email": doctor.email}
    return TokenResponse(
        access_token=create_access_token(str(doctor.id), claims),
        refresh_token=create_refresh_token(str(doctor.id)),
        expires_in_minutes=settings.jwt_expire_minutes,
        doctor=DoctorOut.model_validate(doctor),
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    doctor = await db.scalar(select(Doctor).where(Doctor.email == payload.email.lower()))

    # Same error whether the account is missing, deactivated or the password is
    # wrong, so the endpoint cannot be used to enumerate staff accounts.
    if doctor is None or not doctor.is_active:
        logger.info("Login rejected for %s", payload.email)
        raise INVALID_CREDENTIALS

    if not verify_password(payload.password, doctor.password_hash):
        logger.info("Login failed for doctor %s", doctor.id)
        raise INVALID_CREDENTIALS

    return _tokens_for(doctor)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    claims = decode_refresh_token(payload.refresh_token)
    if not claims or not claims.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or has expired. Please sign in again.",
        )

    try:
        doctor_id = uuid.UUID(str(claims["sub"]))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token is malformed."
        )

    doctor = await db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if doctor is None or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="This account is no longer active."
        )

    return _tokens_for(doctor)


@router.get("/me", response_model=DoctorOut)
async def me(doctor: CurrentDoctor) -> DoctorOut:
    return DoctorOut.model_validate(doctor)
