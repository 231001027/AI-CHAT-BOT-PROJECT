"""
Report generation and download.

The PDF is produced on the server from the stored report_json, so the document a
patient downloads is reproducible from the database record rather than from
whatever rendered in their browser.
"""

from __future__ import annotations

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_db
from app.models import (
    AiConversation,
    Condition,
    MedicalReport,
    Patient,
    PatientAnswer,
    PatientProfile,
    Question,
    QuestionnaireSession,
    TestCatalog,
    TreatmentCategory,
    TreatmentPlan,
)
from app.models.enums import ExplanationSource
from app.schemas.clinical import GenerateReportRequest, ReportOut
from app.services.report_service import build_report_json, render_pdf, report_filename

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/generate", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: GenerateReportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportOut:
    """Build report_json from the stored plan and render it to a PDF."""
    settings = get_settings()

    session = await db.scalar(
        select(QuestionnaireSession).where(QuestionnaireSession.id == payload.session_id)
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    plan = await db.scalar(
        select(TreatmentPlan)
        .where(TreatmentPlan.session_id == session.id)
        .order_by(TreatmentPlan.generated_at.desc())
    )
    if plan is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Generate the recommendations for this session before requesting a report."
            ),
        )

    patient = await db.scalar(select(Patient).where(Patient.id == session.patient_id))
    if patient is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Patient not found.")

    profile = await db.scalar(
        select(PatientProfile)
        .where(PatientProfile.patient_id == patient.id)
        .order_by(PatientProfile.created_at.desc())
    )
    category = (
        await db.scalar(select(TreatmentCategory).where(TreatmentCategory.id == session.category_id))
        if session.category_id
        else None
    )
    condition = (
        await db.scalar(select(Condition).where(Condition.id == session.condition_id))
        if session.condition_id
        else None
    )

    answers = (
        await db.execute(
            select(PatientAnswer)
            .where(PatientAnswer.session_id == session.id)
            .order_by(PatientAnswer.answered_at)
        )
    ).scalars().all()

    texts: dict[uuid.UUID, str] = {}
    if answers:
        rows = (
            await db.execute(
                select(Question.id, Question.text).where(
                    Question.id.in_([a.question_id for a in answers])
                )
            )
        ).all()
        texts = {row[0]: row[1] for row in rows}

    tests = list(plan.recommended_tests or [])

    # Attach catalogue preparation notes where the code matches.
    if tests:
        catalog = (
            await db.execute(
                select(TestCatalog).where(
                    TestCatalog.code.in_([t.get("test_code", "").upper() for t in tests])
                )
            )
        ).scalars().all()
        by_code = {c.code.upper(): c for c in catalog}
        for test in tests:
            entry = by_code.get(str(test.get("test_code", "")).upper())
            if entry is not None:
                test["preparation"] = entry.preparation

    # Only grounded or admin-approved explanations already logged for this
    # session are embedded; nothing new is generated during report building, so
    # an LLM outage cannot block a download.
    explanations: dict[str, str] = {}
    if payload.include_explanations:
        logged = (
            await db.execute(
                select(AiConversation)
                .where(AiConversation.session_id == session.id)
                .order_by(AiConversation.created_at)
            )
        ).scalars().all()
        by_name = {
            row.recommended_test_name.strip().lower(): row.response_text
            for row in logged
            if row.source
            in {ExplanationSource.RAG.value, ExplanationSource.STATIC_FALLBACK.value}
        }
        for test in tests:
            match = by_name.get(str(test.get("test_name", "")).strip().lower())
            if match:
                explanations[str(test.get("test_code", ""))] = match

    report_json = build_report_json(
        patient={
            "name": patient.name,
            "age": patient.age,
            "gender": patient.gender,
            "district": patient.district,
            "phone": patient.phone,
            "user_type": patient.user_type,
            "flow_type": profile.flow_type if profile else None,
            "child_subtype": profile.child_subtype if profile else None,
        },
        category={"name": category.name} if category else None,
        condition={"name": condition.name, "description": condition.description}
        if condition
        else None,
        answers=[
            {
                "question_text": texts.get(a.question_id, a.question_key),
                "question_key": a.question_key,
                "answer_label": a.answer_label,
                "answer_value": a.answer_value,
            }
            for a in answers
        ],
        recommended_tests=tests,
        general_recommendations=list(plan.general_recommendations or []),
        explanations=explanations,
        session_id=str(session.id),
    )

    report = MedicalReport(
        patient_id=patient.id,
        session_id=session.id,
        plan_id=plan.id,
        report_json=report_json,
    )
    db.add(report)
    await db.flush()

    # A PDF failure must not lose the report: the JSON is already stored and the
    # UI can render an on-screen version.
    try:
        target = settings.report_storage_path / report_filename(patient.name, str(session.id))
        render_pdf(report_json, target)
        report.pdf_path = str(target)
    except RuntimeError as exc:
        report.pdf_path = None
        report_json.setdefault("meta", {})["pdf_error"] = str(exc)

    await db.flush()

    out = ReportOut.model_validate(report)
    out.download_url = f"/api/reports/{report.id}/download"
    return out


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReportOut:
    report = await _load(db, report_id)
    out = ReportOut.model_validate(report)
    out.download_url = f"/api/reports/{report.id}/download"
    return out


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FileResponse:
    report = await _load(db, report_id)

    if not report.pdf_path:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "The PDF for this report is not available. The report content can "
                "still be viewed on screen."
            ),
        )

    from pathlib import Path

    path = Path(report.pdf_path)
    if not path.exists():
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="The report file is no longer on the server. Please generate it again.",
        )

    patient_name = (report.report_json or {}).get("patient", {}).get("name", "patient")
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=report_filename(patient_name, str(report.session_id)),
    )


async def _load(db: AsyncSession, report_id: uuid.UUID) -> MedicalReport:
    report = await db.scalar(select(MedicalReport).where(MedicalReport.id == report_id))
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report
