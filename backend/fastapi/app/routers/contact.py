"""Contact form persistence endpoint."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ContactMessage
from app.schemas import ContactCreate, ContactOut

logger = logging.getLogger("hearconnect.contact")

router = APIRouter(prefix="/api", tags=["Contact"])


@router.post("/contact", response_model=ContactOut, status_code=201)
def create_contact_message(body: ContactCreate, db: Session = Depends(get_db)):
    """Save a contact form submission from the Contact page."""
    row = ContactMessage(**body.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    logger.info("contact message saved | id=%s | email=%s", row.id, row.email)
    return {"id": row.id, "created_at": row.created_at, "status": "received"}
