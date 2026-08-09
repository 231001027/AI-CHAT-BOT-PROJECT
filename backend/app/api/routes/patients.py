"""
Patient registration, portal login and lookup.

Patients receive a User ID (e.g. ``123/2026``) at registration. The password for
the patient portal is their date of birth. Listing all patients remains admin-only.
"""

from __future__ import annotations

import re
import uuid
from datetime import date, datetime, timezone
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminDoctor
from app.db.session import get_db
from app.models import Patient, PatientProfile
from app.models.enums import AgeBand, ClinicalDepartment, FlowType, UserType
from app.schemas.clinical import (
    PatientListResponse,
    PatientLoginRequest,
    PatientOut,
    PatientProfileOut,
    PatientRegisterRequest,
    PatientSignupRequest,
    PatientUpdateRequest,
)

router = APIRouter(prefix="/api/patients", tags=["patients"])

# Upper age bounds in years for inferring a child's subtype.
_SUBTYPE_BOUNDS: tuple[tuple[float, AgeBand], ...] = (
    (0.5, AgeBand.NEWBORN),
    (2.5, AgeBand.INFANT_TODDLER),
    (5.0, AgeBand.PRESCHOOL),
)
# Ages strictly below this use the child pathway; this age and above are adult.
# Clinic rule: under 13 = child, 13+ = adult.
CHILD_AGE_LIMIT = 13

INVALID_PATIENT_LOGIN = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Incorrect User ID or date of birth.",
)


def infer_flow_type(age: int, relationship: UserType) -> FlowType:
    """
    Decide the pathway.

    Age is the deciding factor rather than who is filling the form, because an
    adult can register on behalf of an adult relative. ``my_child`` always uses
    the child pathway (guardians register children under 13 via age categories).
    """
    if relationship is UserType.MY_CHILD:
        return FlowType.CHILD
    return FlowType.CHILD if age < CHILD_AGE_LIMIT else FlowType.ADULT


def infer_child_subtype(age: int) -> AgeBand:
    """Map a child's age in years to the screening age band."""
    for upper, band in _SUBTYPE_BOUNDS:
        if age < upper:
            return band
    return AgeBand.SCHOOL_AGE


def parse_dob_password(raw: str) -> Optional[date]:
    """Accept YYYY-MM-DD, DD/MM/YYYY or DD-MM-YYYY as the portal password."""
    text = (raw or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


async def allocate_user_code(db: AsyncSession, *, year: Optional[int] = None) -> str:
    """
    Next clinic User ID for the calendar year, e.g. ``123/2026``.

    Sequence is per year so ids stay short and readable at the front desk.
    """
    year = year or date.today().year
    suffix = f"/{year}"
    codes = (
        await db.execute(
            select(Patient.user_code).where(Patient.user_code.like(f"%{suffix}"))
        )
    ).scalars().all()

    max_n = 0
    for code in codes:
        if not code:
            continue
        match = re.match(rf"^(\d+){re.escape(suffix)}$", code.strip())
        if match:
            max_n = max(max_n, int(match.group(1)))
    return f"{max_n + 1}/{year}"


def _to_out(patient: Patient, profile: Optional[PatientProfile]) -> PatientOut:
    out = PatientOut.model_validate(patient)
    if profile is not None:
        out.profile = PatientProfileOut.model_validate(profile)
    return out


async def _latest_profile(db: AsyncSession, patient_id: uuid.UUID) -> Optional[PatientProfile]:
    return await db.scalar(
        select(PatientProfile)
        .where(PatientProfile.patient_id == patient_id)
        .order_by(PatientProfile.created_at.desc())
    )


@router.post("", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def register_patient(
    payload: PatientRegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientOut:
    """Register a patient, issue a User ID, and create their flow profile."""
    flow_type = payload.flow_type or infer_flow_type(payload.age, payload.relationship)

    child_subtype: Optional[AgeBand] = None
    if flow_type is FlowType.CHILD:
        child_subtype = payload.child_subtype or infer_child_subtype(payload.age)
        # Guardian consent is a precondition for processing a child's data.
        if not payload.consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Guardian consent is required before registering a child. "
                    "Please confirm consent to continue."
                ),
            )

    user_code = await allocate_user_code(db, year=date.today().year)

    patient = Patient(
        name=payload.name.strip(),
        age=payload.age,
        gender=payload.gender.strip(),
        district=payload.district.strip(),
        phone=payload.phone,
        user_type=payload.relationship.value,
        user_code=user_code,
        date_of_birth=payload.date_of_birth,
    )
    db.add(patient)
    await db.flush()

    profile = PatientProfile(
        patient_id=patient.id,
        flow_type=flow_type.value,
        department=payload.department.value,
        child_subtype=child_subtype.value if child_subtype else None,
        consent_given=payload.consent_given,
        consent_by=(payload.consent_by or "").strip() or None,
        consent_at=datetime.now(timezone.utc) if payload.consent_given else None,
    )
    db.add(profile)
    await db.flush()

    return _to_out(patient, profile)


@router.post("/signup", response_model=PatientOut, status_code=status.HTTP_201_CREATED)
async def signup_patient(
    payload: PatientSignupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientOut:
    """Create an account using User ID + date (password)."""
    dob = parse_dob_password(payload.password)
    if dob is None or dob > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a valid date.",
        )

    today = date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    if age < 0 or age > 120:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Enter a realistic date.",
        )

    # Returning user: same User ID + matching date → continue without recreating.
    if payload.user_id:
        existing = await db.scalar(
            select(Patient).where(Patient.user_code == payload.user_id)
        )
        if existing is not None:
            if existing.date_of_birth == dob:
                profile = await _latest_profile(db, existing.id)
                return _to_out(existing, profile)
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "That User ID is already registered. "
                    "Sign in with the same date, or leave User ID blank to get a new one."
                ),
            )
        user_code = payload.user_id
    else:
        user_code = await allocate_user_code(db, year=today.year)

    flow_type = infer_flow_type(age, payload.relationship)
    child_subtype: Optional[AgeBand] = None
    if flow_type is FlowType.CHILD:
        child_subtype = infer_child_subtype(age)
        if not payload.consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Guardian consent is required before registering a child.",
            )

    patient = Patient(
        name=f"Patient {user_code}",
        age=age,
        gender="prefer_not_to_say",
        district="Not specified",
        phone=None,
        user_type=payload.relationship.value,
        user_code=user_code,
        date_of_birth=dob,
    )
    db.add(patient)
    await db.flush()

    profile = PatientProfile(
        patient_id=patient.id,
        flow_type=flow_type.value,
        department=payload.department.value,
        child_subtype=child_subtype.value if child_subtype else None,
        consent_given=payload.consent_given,
        consent_by=(payload.consent_by or "").strip() or None,
        consent_at=datetime.now(timezone.utc) if payload.consent_given else None,
    )
    db.add(profile)
    await db.flush()

    return _to_out(patient, profile)


@router.post("/login", response_model=PatientOut)
async def login_patient(
    payload: PatientLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientOut:
    """Sign in with User ID and date of birth (password)."""
    user_code = payload.user_id.strip()
    dob = parse_dob_password(payload.password)
    if dob is None:
        raise INVALID_PATIENT_LOGIN

    patient = await db.scalar(select(Patient).where(Patient.user_code == user_code))
    if patient is None or patient.date_of_birth is None:
        raise INVALID_PATIENT_LOGIN
    if patient.date_of_birth != dob:
        raise INVALID_PATIENT_LOGIN

    profile = await _latest_profile(db, patient.id)
    return _to_out(patient, profile)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(
    patient_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientOut:
    patient = await db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    profile = await _latest_profile(db, patient_id)
    return _to_out(patient, profile)


@router.patch("/{patient_id}", response_model=PatientOut)
async def update_patient(
    patient_id: uuid.UUID,
    payload: PatientUpdateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PatientOut:
    """Fill in registration details after sign-in and relationship selection."""
    patient = await db.scalar(select(Patient).where(Patient.id == patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    flow_type = payload.flow_type or infer_flow_type(payload.age, payload.relationship)
    child_subtype: Optional[AgeBand] = None
    if flow_type is FlowType.CHILD:
        child_subtype = payload.child_subtype or infer_child_subtype(payload.age)
        if not payload.consent_given:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Guardian consent is required before registering a child. "
                    "Please confirm consent to continue."
                ),
            )

    patient.name = payload.name.strip()
    patient.age = payload.age
    patient.gender = payload.gender.strip()
    patient.district = payload.district.strip()
    patient.phone = payload.phone
    patient.user_type = payload.relationship.value
    # Portal password is date_of_birth from sign-up — never overwrite it here.
    if patient.date_of_birth is None:
        patient.date_of_birth = payload.date_of_birth

    profile = await _latest_profile(db, patient_id)
    if profile is None:
        profile = PatientProfile(patient_id=patient.id)
        db.add(profile)

    profile.flow_type = flow_type.value
    profile.department = payload.department.value
    profile.child_subtype = child_subtype.value if child_subtype else None
    profile.consent_given = payload.consent_given
    profile.consent_by = (payload.consent_by or "").strip() or None
    if payload.consent_given:
        profile.consent_at = datetime.now(timezone.utc)

    await db.flush()
    return _to_out(patient, profile)


@router.get("", response_model=PatientListResponse)
async def list_patients(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    search: Annotated[Optional[str], Query(max_length=120)] = None,
    district: Annotated[Optional[str], Query(max_length=120)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PatientListResponse:
    """Admin-only listing. Returns a total so the UI can paginate."""
    filters = []
    if search:
        term = f"%{search.strip()}%"
        filters.append(
            or_(
                Patient.name.ilike(term),
                Patient.phone.ilike(term),
                Patient.user_code.ilike(term),
            )
        )
    if district:
        filters.append(Patient.district.ilike(f"%{district.strip()}%"))

    count_stmt = select(func.count()).select_from(Patient)
    list_stmt = select(Patient).order_by(Patient.created_at.desc()).limit(limit).offset(offset)
    for condition in filters:
        count_stmt = count_stmt.where(condition)
        list_stmt = list_stmt.where(condition)

    total = await db.scalar(count_stmt) or 0
    patients = (await db.execute(list_stmt)).scalars().all()

    if not patients:
        return PatientListResponse(total=total, items=[])

    profiles = (
        await db.execute(
            select(PatientProfile).where(
                PatientProfile.patient_id.in_([p.id for p in patients])
            )
        )
    ).scalars().all()
    by_patient = {p.patient_id: p for p in profiles}

    return PatientListResponse(
        total=total,
        items=[_to_out(p, by_patient.get(p.id)) for p in patients],
    )
