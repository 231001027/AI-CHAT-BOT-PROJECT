"""Assessment form persistence endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Assessment
from app.schemas import AssessmentCreate, AssessmentOut

logger = logging.getLogger("hearconnect.assessments")

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("", response_model=AssessmentOut, status_code=201)
def create_assessment(body: AssessmentCreate, db: Session = Depends(get_db)):
    """Save an assessment form submission from the guided wizard."""
    row = Assessment(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("assessment saved | id=%s | routed_to=%s", row.id, row.routed_to)
    return row


@router.get("", response_model=list[AssessmentOut])
def list_assessments(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List recent assessments (newest first)."""
    return (
        db.query(Assessment)
        .order_by(Assessment.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: str, db: Session = Depends(get_db)):
    row = db.get(Assessment, assessment_id)
    if not row:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return row
