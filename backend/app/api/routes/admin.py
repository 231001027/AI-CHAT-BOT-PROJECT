"""
Admin routes: question bank, clinical rules, staff, RAG corpus and audit logs.

Every route here requires an admin token. Editing questions or rules changes what
future patients are told, so it is held to a higher bar than ordinary clinical
access.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import AdminDoctor
from app.config import get_settings
from app.core.security import hash_password
from app.db.session import get_db
from app.models import (
    AiConversation,
    Appointment,
    ClinicalRule,
    Condition,
    Doctor,
    EscalationTicket,
    HospitalDocument,
    MedicalReport,
    Patient,
    Question,
    QuestionnaireSession,
    QuestionOption,
    RuleRecommendedTest,
    StaticExplanation,
    TreatmentCategory,
    TreatmentPlan,
)
from app.models.enums import (
    AppointmentStatus,
    DocumentCategory,
    DocumentStatus,
    EscalationStatus,
    ExplanationSource,
    SessionStatus,
)
from app.schemas.clinical import (
    AiConversationOut,
    CategoryCreate,
    CategoryOut,
    CategoryUpdate,
    ConditionCreate,
    ConditionOut,
    ConditionUpdate,
    DashboardStats,
    DocumentListResponse,
    DocumentOut,
    DoctorCreate,
    DoctorOut,
    DoctorUpdate,
    OptionCreate,
    OptionOut,
    OptionUpdate,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    ReportOut,
    RuleCreate,
    RuleOut,
    RuleUpdate,
    RuleValidateRequest,
    RuleValidateResponse,
    StaticExplanationIn,
    StaticExplanationOut,
)
from app.services.ai.rag_pipeline import index_document, rag_status, remove_document_vectors
from app.services.clinical_rules import RuleEvaluationError, evaluate_predicate

router = APIRouter(prefix="/api/admin", tags=["admin"])

ALLOWED_UPLOAD_SUFFIXES = {".pdf", ".txt", ".md", ".markdown", ".docx"}
_SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found.")


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    async def count(stmt) -> int:
        return await db.scalar(stmt) or 0

    ai_total = await count(select(func.count()).select_from(AiConversation))
    ai_fallback = await count(
        select(func.count())
        .select_from(AiConversation)
        .where(AiConversation.source == ExplanationSource.STATIC_FALLBACK.value)
    )

    return DashboardStats(
        patients_total=await count(select(func.count()).select_from(Patient)),
        patients_last_7_days=await count(
            select(func.count()).select_from(Patient).where(Patient.created_at >= week_ago)
        ),
        sessions_total=await count(select(func.count()).select_from(QuestionnaireSession)),
        sessions_completed=await count(
            select(func.count())
            .select_from(QuestionnaireSession)
            .where(QuestionnaireSession.status == SessionStatus.COMPLETED.value)
        ),
        plans_generated=await count(select(func.count()).select_from(TreatmentPlan)),
        reports_generated=await count(select(func.count()).select_from(MedicalReport)),
        ai_explanations=ai_total,
        # Surfaced prominently because a high fallback rate means the corpus is
        # too thin for the tests patients are actually being recommended.
        ai_fallback_rate=round(ai_fallback / ai_total, 3) if ai_total else 0.0,
        documents_indexed=await count(
            select(func.count())
            .select_from(HospitalDocument)
            .where(HospitalDocument.vector_indexed.is_(True))
        ),
        documents_total=await count(select(func.count()).select_from(HospitalDocument)),
        appointments_upcoming=await count(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.status.in_(
                    [
                        AppointmentStatus.REQUESTED.value,
                        AppointmentStatus.CONFIRMED.value,
                        AppointmentStatus.RESCHEDULED.value,
                    ]
                )
            )
        ),
        escalations_open=await count(
            select(func.count())
            .select_from(EscalationTicket)
            .where(EscalationTicket.status == EscalationStatus.OPEN.value)
        ),
        rules_active=await count(
            select(func.count()).select_from(ClinicalRule).where(ClinicalRule.is_active.is_(True))
        ),
        questions_active=await count(
            select(func.count()).select_from(Question).where(Question.is_active.is_(True))
        ),
    )


@router.get("/rag-status")
async def get_rag_status(_admin: AdminDoctor) -> dict[str, object]:
    return await rag_status()


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get("/categories", response_model=list[CategoryOut])
async def admin_list_categories(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[CategoryOut]:
    rows = (
        await db.execute(
            select(TreatmentCategory).order_by(
                TreatmentCategory.flow_type,
                TreatmentCategory.display_order,
                TreatmentCategory.name,
            )
        )
    ).scalars().all()
    return [CategoryOut.model_validate(r) for r in rows]


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryOut:
    if await db.scalar(select(TreatmentCategory).where(TreatmentCategory.slug == payload.slug)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with slug '{payload.slug}' already exists.",
        )
    row = TreatmentCategory(
        slug=payload.slug,
        name=payload.name,
        flow_type=payload.flow_type.value,
        department=payload.department.value,
        description=payload.description,
        display_order=payload.display_order,
    )
    db.add(row)
    await db.flush()
    return CategoryOut.model_validate(row)


@router.patch("/categories/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CategoryOut:
    row = await db.scalar(select(TreatmentCategory).where(TreatmentCategory.id == category_id))
    if row is None:
        raise _not_found("Category")

    data = payload.model_dump(exclude_unset=True)
    if "flow_type" in data and data["flow_type"] is not None:
        data["flow_type"] = data["flow_type"].value
    if "department" in data and data["department"] is not None:
        data["department"] = data["department"].value
    for key, value in data.items():
        setattr(row, key, value)
    await db.flush()
    return CategoryOut.model_validate(row)


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_category(
    category_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(TreatmentCategory).where(TreatmentCategory.id == category_id))
    if row is None:
        raise _not_found("Category")
    await db.delete(row)


# ---------------------------------------------------------------------------
# Conditions
# ---------------------------------------------------------------------------


@router.get("/conditions", response_model=list[ConditionOut])
async def admin_list_conditions(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: Annotated[Optional[uuid.UUID], Query()] = None,
) -> list[ConditionOut]:
    stmt = select(Condition).order_by(Condition.display_order, Condition.name)
    if category_id is not None:
        stmt = stmt.where(Condition.category_id == category_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [ConditionOut.model_validate(r) for r in rows]


@router.post("/conditions", response_model=ConditionOut, status_code=status.HTTP_201_CREATED)
async def create_condition(
    payload: ConditionCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConditionOut:
    if not await db.scalar(
        select(TreatmentCategory).where(TreatmentCategory.id == payload.category_id)
    ):
        raise _not_found("Category")
    if await db.scalar(select(Condition).where(Condition.slug == payload.slug)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A condition with slug '{payload.slug}' already exists.",
        )

    row = Condition(
        category_id=payload.category_id,
        slug=payload.slug,
        name=payload.name,
        description=payload.description,
        display_order=payload.display_order,
    )
    db.add(row)
    await db.flush()
    return ConditionOut.model_validate(row)


@router.patch("/conditions/{condition_id}", response_model=ConditionOut)
async def update_condition(
    condition_id: uuid.UUID,
    payload: ConditionUpdate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ConditionOut:
    row = await db.scalar(select(Condition).where(Condition.id == condition_id))
    if row is None:
        raise _not_found("Condition")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    await db.flush()
    return ConditionOut.model_validate(row)


@router.delete("/conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_condition(
    condition_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(Condition).where(Condition.id == condition_id))
    if row is None:
        raise _not_found("Condition")
    await db.delete(row)


# ---------------------------------------------------------------------------
# Questions and options
# ---------------------------------------------------------------------------


@router.get("/questions", response_model=list[QuestionOut])
async def admin_list_questions(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    condition_id: Annotated[Optional[uuid.UUID], Query()] = None,
) -> list[QuestionOut]:
    stmt = (
        select(Question)
        .options(selectinload(Question.options))
        .order_by(Question.display_order, Question.key)
    )
    if condition_id is not None:
        stmt = stmt.where(Question.condition_id == condition_id)

    rows = (await db.execute(stmt)).scalars().all()
    out: list[QuestionOut] = []
    for row in rows:
        item = QuestionOut.model_validate(row)
        item.options = [
            OptionOut.model_validate(o)
            for o in sorted(row.options, key=lambda o: (o.display_order, o.label))
        ]
        out.append(item)
    return out


@router.post("/questions", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
async def create_question(
    payload: QuestionCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuestionOut:
    if not await db.scalar(select(Condition).where(Condition.id == payload.condition_id)):
        raise _not_found("Condition")

    # Rules reference questions by key, so a duplicate key within one condition
    # would make rule behaviour ambiguous.
    clash = await db.scalar(
        select(Question).where(
            Question.condition_id == payload.condition_id, Question.key == payload.key
        )
    )
    if clash is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Key '{payload.key}' is already used by another question in this condition.",
        )

    if payload.is_entry:
        await _clear_entry_flag(db, payload.condition_id)

    row = Question(
        condition_id=payload.condition_id,
        key=payload.key,
        text=payload.text,
        help_text=payload.help_text,
        display_order=payload.display_order,
        question_type=payload.question_type.value,
        is_entry=payload.is_entry,
    )
    db.add(row)
    await db.flush()
    out = QuestionOut.model_validate(row)
    out.options = []
    return out


async def _clear_entry_flag(db: AsyncSession, condition_id: uuid.UUID) -> None:
    """Only one question per condition may be the entry point."""
    rows = (
        await db.execute(
            select(Question).where(
                Question.condition_id == condition_id, Question.is_entry.is_(True)
            )
        )
    ).scalars().all()
    for row in rows:
        row.is_entry = False


@router.patch("/questions/{question_id}", response_model=QuestionOut)
async def update_question(
    question_id: uuid.UUID,
    payload: QuestionUpdate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> QuestionOut:
    row = await db.scalar(
        select(Question).where(Question.id == question_id).options(selectinload(Question.options))
    )
    if row is None:
        raise _not_found("Question")

    data = payload.model_dump(exclude_unset=True)
    if data.get("is_entry"):
        await _clear_entry_flag(db, row.condition_id)
    if "question_type" in data and data["question_type"] is not None:
        data["question_type"] = data["question_type"].value

    for key, value in data.items():
        setattr(row, key, value)
    await db.flush()

    out = QuestionOut.model_validate(row)
    out.options = [
        OptionOut.model_validate(o)
        for o in sorted(row.options, key=lambda o: (o.display_order, o.label))
    ]
    return out


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_question(
    question_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(Question).where(Question.id == question_id))
    if row is None:
        raise _not_found("Question")
    await db.delete(row)


@router.post("/options", response_model=OptionOut, status_code=status.HTTP_201_CREATED)
async def create_option(
    payload: OptionCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OptionOut:
    question = await db.scalar(select(Question).where(Question.id == payload.question_id))
    if question is None:
        raise _not_found("Question")

    await _validate_branch_target(db, question, payload.next_question_id)

    row = QuestionOption(
        question_id=payload.question_id,
        label=payload.label,
        value=payload.value,
        display_order=payload.display_order,
        next_question_id=payload.next_question_id,
        is_terminal=payload.is_terminal,
    )
    db.add(row)
    await db.flush()
    return OptionOut.model_validate(row)


async def _validate_branch_target(
    db: AsyncSession, question: Question, next_question_id: Optional[uuid.UUID]
) -> None:
    """
    Check a branch target is usable.

    A branch may only point at another question in the same condition; pointing
    across conditions would take the patient into an unrelated flow.
    """
    if next_question_id is None:
        return
    if next_question_id == question.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An option cannot branch back to its own question.",
        )
    target = await db.scalar(select(Question).where(Question.id == next_question_id))
    if target is None:
        raise _not_found("Branch target question")
    if target.condition_id != question.condition_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A branch must point to a question within the same condition.",
        )


@router.patch("/options/{option_id}", response_model=OptionOut)
async def update_option(
    option_id: uuid.UUID,
    payload: OptionUpdate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OptionOut:
    row = await db.scalar(select(QuestionOption).where(QuestionOption.id == option_id))
    if row is None:
        raise _not_found("Option")

    data = payload.model_dump(exclude_unset=True)
    if "next_question_id" in data:
        question = await db.scalar(select(Question).where(Question.id == row.question_id))
        if question is not None:
            await _validate_branch_target(db, question, data["next_question_id"])

    for key, value in data.items():
        setattr(row, key, value)
    await db.flush()
    return OptionOut.model_validate(row)


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_option(
    option_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(QuestionOption).where(QuestionOption.id == option_id))
    if row is None:
        raise _not_found("Option")
    await db.delete(row)


# ---------------------------------------------------------------------------
# Clinical rules
# ---------------------------------------------------------------------------


def _collect_fields(node: object, found: set[str]) -> None:
    """Walk a rule definition and gather every field it references."""
    if isinstance(node, dict):
        if "field" in node and isinstance(node["field"], str):
            found.add(node["field"])
        for key in ("all", "any"):
            if isinstance(node.get(key), list):
                for child in node[key]:
                    _collect_fields(child, found)
        if "not" in node:
            _collect_fields(node["not"], found)


@router.post("/rules/validate", response_model=RuleValidateResponse)
async def validate_rule(
    payload: RuleValidateRequest,
    _admin: AdminDoctor,
) -> RuleValidateResponse:
    """
    Dry-run a rule definition before saving it.

    Lets the rule builder catch a malformed predicate, and check the rule fires
    the way the author expects against sample answers.
    """
    fields: set[str] = set()
    _collect_fields(payload.rule_definition, fields)

    try:
        matches = evaluate_predicate(payload.rule_definition, payload.sample_facts)
    except RuleEvaluationError as exc:
        return RuleValidateResponse(
            is_valid=False, error=str(exc), referenced_fields=sorted(fields)
        )

    return RuleValidateResponse(
        is_valid=True,
        matches_sample=matches if payload.sample_facts else None,
        referenced_fields=sorted(fields),
    )


@router.get("/rules", response_model=list[RuleOut])
async def list_rules(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    condition_id: Annotated[Optional[uuid.UUID], Query()] = None,
) -> list[RuleOut]:
    stmt = (
        select(ClinicalRule)
        .options(selectinload(ClinicalRule.tests))
        .order_by(ClinicalRule.priority.desc(), ClinicalRule.name)
    )
    if condition_id is not None:
        stmt = stmt.where(ClinicalRule.condition_id == condition_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [RuleOut.model_validate(r) for r in rows]


@router.post("/rules", response_model=RuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: RuleCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RuleOut:
    if not payload.is_baseline and not payload.rule_definition:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "A rule needs either a definition or the baseline flag. An empty "
                "definition never matches."
            ),
        )
    try:
        evaluate_predicate(payload.rule_definition, {})
    except RuleEvaluationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid rule: {exc}"
        ) from exc

    row = ClinicalRule(
        name=payload.name,
        description=payload.description,
        category_id=payload.category_id,
        condition_id=payload.condition_id,
        rule_definition=payload.rule_definition,
        priority=payload.priority,
        is_baseline=payload.is_baseline,
    )
    db.add(row)
    await db.flush()

    for test in payload.tests:
        db.add(
            RuleRecommendedTest(
                rule_id=row.id,
                test_code=test.test_code.upper(),
                test_name=test.test_name,
                reason_text=test.reason_text,
                display_order=test.display_order,
            )
        )
    await db.flush()
    await db.refresh(row, ["tests"])
    return RuleOut.model_validate(row)


@router.patch("/rules/{rule_id}", response_model=RuleOut)
async def update_rule(
    rule_id: uuid.UUID,
    payload: RuleUpdate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RuleOut:
    row = await db.scalar(
        select(ClinicalRule)
        .where(ClinicalRule.id == rule_id)
        .options(selectinload(ClinicalRule.tests))
    )
    if row is None:
        raise _not_found("Rule")

    data = payload.model_dump(exclude_unset=True)
    tests = data.pop("tests", None)

    if "rule_definition" in data and data["rule_definition"] is not None:
        try:
            evaluate_predicate(data["rule_definition"], {})
        except RuleEvaluationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid rule: {exc}"
            ) from exc

    for key, value in data.items():
        setattr(row, key, value)

    if tests is not None:
        # Replace wholesale: the rule builder posts the full list each save.
        for existing in list(row.tests):
            await db.delete(existing)
        await db.flush()
        for test in tests:
            db.add(
                RuleRecommendedTest(
                    rule_id=row.id,
                    test_code=str(test["test_code"]).upper(),
                    test_name=test["test_name"],
                    reason_text=test.get("reason_text", ""),
                    display_order=test.get("display_order", 0),
                )
            )

    await db.flush()
    await db.refresh(row, ["tests"])
    return RuleOut.model_validate(row)


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_rule(
    rule_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(ClinicalRule).where(ClinicalRule.id == rule_id))
    if row is None:
        raise _not_found("Rule")
    await db.delete(row)


# ---------------------------------------------------------------------------
# Staff accounts
# ---------------------------------------------------------------------------


@router.get("/doctors", response_model=list[DoctorOut])
async def list_doctors(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[DoctorOut]:
    rows = (await db.execute(select(Doctor).order_by(Doctor.name))).scalars().all()
    return [DoctorOut.model_validate(r) for r in rows]


@router.post("/doctors", response_model=DoctorOut, status_code=status.HTTP_201_CREATED)
async def create_doctor(
    payload: DoctorCreate,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorOut:
    email = payload.email.lower()
    if await db.scalar(select(Doctor).where(Doctor.email == email)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    row = Doctor(
        name=payload.name,
        email=email,
        specialization=payload.specialization,
        phone=payload.phone,
        role=payload.role.value,
        password_hash=hash_password(payload.password),
    )
    db.add(row)
    await db.flush()
    return DoctorOut.model_validate(row)


@router.patch("/doctors/{doctor_id}", response_model=DoctorOut)
async def update_doctor(
    doctor_id: uuid.UUID,
    payload: DoctorUpdate,
    admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DoctorOut:
    row = await db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if row is None:
        raise _not_found("Doctor")

    data = payload.model_dump(exclude_unset=True)

    # Guard against an admin locking themselves out.
    if row.id == admin.id:
        if data.get("is_active") is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate your own account.",
            )
        if "role" in data and data["role"] is not None and data["role"].value != row.role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot change your own role.",
            )

    if password := data.pop("password", None):
        row.password_hash = hash_password(password)
    if "role" in data and data["role"] is not None:
        data["role"] = data["role"].value

    for key, value in data.items():
        setattr(row, key, value)
    await db.flush()
    return DoctorOut.model_validate(row)


@router.delete("/doctors/{doctor_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def deactivate_doctor(
    doctor_id: uuid.UUID,
    admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Deactivates rather than deletes, so uploads and audit rows keep their author."""
    row = await db.scalar(select(Doctor).where(Doctor.id == doctor_id))
    if row is None:
        raise _not_found("Doctor")
    if row.id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )
    row.is_active = False


# ---------------------------------------------------------------------------
# RAG corpus
# ---------------------------------------------------------------------------


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentListResponse:
    rows = (
        await db.execute(select(HospitalDocument).order_by(HospitalDocument.uploaded_at.desc()))
    ).scalars().all()
    health = await rag_status()
    return DocumentListResponse(
        total=len(rows),
        items=[DocumentOut.model_validate(r) for r in rows],
        indexing_available=bool(
            health.get("embeddings_available") and health.get("vector_store_available")
        ),
    )


@router.post("/documents/upload", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
async def upload_document(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: Annotated[UploadFile, File()],
    title: Annotated[str, Form(min_length=2, max_length=300)],
    category: Annotated[DocumentCategory, Form()] = DocumentCategory.GUIDELINE,
    test_tags: Annotated[str, Form()] = "",
) -> DocumentOut:
    """
    Store a document and index it for retrieval.

    ``test_tags`` is a comma-separated list of test codes the document explains;
    it biases retrieval toward the right document for a given test.
    """
    settings = get_settings()

    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_UPLOAD_SUFFIXES))}.",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="The uploaded file is empty."
        )
    if len(contents) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)} MB limit.",
        )

    document_id = uuid.uuid4()
    safe_name = _SAFE_FILENAME.sub("_", Path(file.filename or "document").name)
    target = settings.document_storage_path / f"{document_id}_{safe_name}"
    target.write_bytes(contents)

    row = HospitalDocument(
        id=document_id,
        title=title.strip(),
        category=category.value,
        file_path=str(target),
        original_filename=file.filename,
        content_type=file.content_type,
        size_bytes=len(contents),
        test_tags=[t.strip().upper() for t in test_tags.split(",") if t.strip()],
        uploaded_by=_admin.id,
        status=DocumentStatus.UPLOADED.value,
    )
    db.add(row)
    await db.flush()

    # Indexed inline so the admin sees the outcome immediately. A failure marks
    # the row rather than rejecting the upload, so the file is never lost.
    await index_document(db, row)
    await db.refresh(row)
    return DocumentOut.model_validate(row)


@router.post("/documents/{document_id}/reindex", response_model=DocumentOut)
async def reindex_document(
    document_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DocumentOut:
    row = await db.scalar(select(HospitalDocument).where(HospitalDocument.id == document_id))
    if row is None:
        raise _not_found("Document")
    await index_document(db, row)
    await db.refresh(row)
    return DocumentOut.model_validate(row)


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response, response_model=None)
async def delete_document(
    document_id: uuid.UUID,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    row = await db.scalar(select(HospitalDocument).where(HospitalDocument.id == document_id))
    if row is None:
        raise _not_found("Document")

    await remove_document_vectors(document_id)
    try:
        Path(row.file_path).unlink(missing_ok=True)
    except OSError:
        # A leftover file is preferable to failing the delete.
        pass
    await db.delete(row)


# ---------------------------------------------------------------------------
# Static fallback explanations
# ---------------------------------------------------------------------------


@router.get("/static-explanations", response_model=list[StaticExplanationOut])
async def list_static_explanations(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[StaticExplanationOut]:
    rows = (
        await db.execute(select(StaticExplanation).order_by(StaticExplanation.test_code))
    ).scalars().all()
    return [StaticExplanationOut.model_validate(r) for r in rows]


@router.put("/static-explanations", response_model=StaticExplanationOut)
async def upsert_static_explanation(
    payload: StaticExplanationIn,
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StaticExplanationOut:
    """Create or replace the approved fallback wording for a test."""
    code = payload.test_code.strip().upper()
    row = await db.scalar(select(StaticExplanation).where(StaticExplanation.test_code == code))
    if row is None:
        row = StaticExplanation(
            test_code=code, test_name=payload.test_name, explanation=payload.explanation
        )
        db.add(row)
    else:
        row.test_name = payload.test_name
        row.explanation = payload.explanation
    await db.flush()
    return StaticExplanationOut.model_validate(row)


# ---------------------------------------------------------------------------
# Audit logs and reports
# ---------------------------------------------------------------------------


@router.get("/ai-logs", response_model=list[AiConversationOut])
async def ai_logs(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    source: Annotated[Optional[ExplanationSource], Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[AiConversationOut]:
    stmt = (
        select(AiConversation)
        .order_by(AiConversation.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if source is not None:
        stmt = stmt.where(AiConversation.source == source.value)
    rows = (await db.execute(stmt)).scalars().all()
    return [AiConversationOut.model_validate(r) for r in rows]


@router.get("/reports", response_model=list[ReportOut])
async def admin_list_reports(
    _admin: AdminDoctor,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[ReportOut]:
    rows = (
        await db.execute(
            select(MedicalReport)
            .order_by(MedicalReport.generated_at.desc())
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()

    out: list[ReportOut] = []
    for row in rows:
        item = ReportOut.model_validate(row)
        item.download_url = f"/api/reports/{row.id}/download"
        out.append(item)
    return out
