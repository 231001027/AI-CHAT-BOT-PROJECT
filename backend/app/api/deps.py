"""
Shared FastAPI dependencies for staff authentication.

Patient-facing routes are deliberately unauthenticated: registration is per
visit, with no patient accounts. Everything under /api/admin, plus the AI audit
trail, requires a staff token.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import Doctor
from app.models.enums import ADMIN_ROLES

# Compared as plain strings: Enum hashes on member name, so a frozenset of
# StrEnum members would not match the value stored on the row.
ADMIN_ROLE_VALUES: frozenset[str] = frozenset(role.value for role in ADMIN_ROLES)

# auto_error=False so a missing header produces our own 401 with a clear message
# rather than FastAPI's bare "Not authenticated".
bearer_scheme = HTTPBearer(auto_error=False)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated. Sign in with a staff account.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_doctor(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Doctor:
    """Resolve the signed-in staff member, or raise 401."""
    if credentials is None or not credentials.credentials:
        raise CREDENTIALS_EXCEPTION

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise CREDENTIALS_EXCEPTION

    subject = payload.get("sub")
    if not subject:
        raise CREDENTIALS_EXCEPTION

    try:
        doctor_id = uuid.UUID(str(subject))
    except (ValueError, TypeError):
        raise CREDENTIALS_EXCEPTION

    doctor = await db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if doctor is None or not doctor.is_active:
        # A deactivated account must stop working immediately, even while it
        # still holds an unexpired token.
        raise CREDENTIALS_EXCEPTION

    return doctor


CurrentDoctor = Annotated[Doctor, Depends(get_current_doctor)]


async def require_admin(doctor: CurrentDoctor) -> Doctor:
    """
    Restrict a route to admins.

    Editing the question bank or clinical rules changes what every future patient
    is told, so it is held to a higher bar than ordinary clinical access.
    """
    if doctor.role not in ADMIN_ROLE_VALUES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires an administrator account.",
        )
    return doctor


AdminDoctor = Annotated[Doctor, Depends(require_admin)]
