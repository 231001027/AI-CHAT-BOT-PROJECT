"""
Report generation.

The PDF is built on the server from the stored ``report_json`` so the document is
reproducible from the database alone, rather than depending on whatever happened
to render in a browser. ``build_report_json`` is pure and unit-testable; only
``render_pdf`` touches ReportLab.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

logger = logging.getLogger("nipmed.reports")

DEPARTMENT_NAME = "Department of Speech, Hearing and Communication"
INSTITUTE_NAME = "National Institute for Empowerment of Persons with Multiple Disabilities (NIEPMD)"
INSTITUTE_ADDRESS = "East Coast Road, Muttukadu, Kovalam Post, Chennai 603112"
DEPARTMENT_PHONE = "044-2452-0639"

SAFETY_DISCLAIMER = (
    "This document is a guidance summary generated from the answers given. It is "
    "for education only. It is NOT a diagnosis, NOT a prescription and NOT a "
    "substitute for examination by a qualified audiologist or doctor. The tests "
    "listed are suggestions to discuss at your appointment. Only a qualified "
    "clinician can diagnose a condition after examining you and reviewing your "
    "results."
)

URGENT_NOTICE = (
    "If you experience sudden hearing loss, severe ear pain, bleeding or discharge "
    "from the ear, or any difficulty breathing or swallowing, go to the nearest "
    "hospital emergency department immediately. Do not wait for this appointment."
)


def build_report_json(
    *,
    patient: dict[str, Any],
    category: Optional[dict[str, Any]],
    condition: Optional[dict[str, Any]],
    answers: Sequence[dict[str, Any]],
    recommended_tests: Sequence[dict[str, Any]],
    general_recommendations: Sequence[str],
    explanations: Optional[dict[str, str]] = None,
    session_id: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """
    Assemble the structured content backing the PDF.

    Everything the document shows is captured here, so regenerating the PDF from
    this dictionary always produces the same clinical content even if the
    question bank or rules change later.
    """
    moment = generated_at or datetime.now(timezone.utc)
    return {
        "meta": {
            "institute": INSTITUTE_NAME,
            "department": DEPARTMENT_NAME,
            "address": INSTITUTE_ADDRESS,
            "phone": DEPARTMENT_PHONE,
            "generated_at": moment.isoformat(),
            "session_id": session_id,
            "document_type": "Pre-consultation guidance summary",
        },
        "patient": {
            "name": patient.get("name", ""),
            "age": patient.get("age"),
            "gender": patient.get("gender", ""),
            "district": patient.get("district", ""),
            "phone": patient.get("phone"),
            "relationship": patient.get("user_type"),
            "flow_type": patient.get("flow_type"),
            "child_subtype": patient.get("child_subtype"),
        },
        "presenting": {
            "category": (category or {}).get("name"),
            "condition": (condition or {}).get("name"),
            "condition_description": (condition or {}).get("description"),
        },
        "answers": [
            {
                "question": a.get("question_text") or a.get("question_key", ""),
                "answer": a.get("answer_label") or a.get("answer_value", ""),
            }
            for a in answers
        ],
        "recommended_tests": [
            {
                "test_code": t.get("test_code", ""),
                "test_name": t.get("test_name", ""),
                "reason_text": t.get("reason_text", ""),
                "preparation": t.get("preparation"),
                "explanation": (explanations or {}).get(t.get("test_code", "")),
            }
            for t in recommended_tests
        ],
        "general_recommendations": list(general_recommendations),
        "disclaimer": SAFETY_DISCLAIMER,
        "urgent_notice": URGENT_NOTICE,
    }


def render_pdf(report: dict[str, Any], output_path: Path | str) -> Path:
    """
    Render ``report_json`` to a PDF.

    Raises RuntimeError if ReportLab is not installed, so the caller can still
    return the JSON and let the UI offer an on-screen report.
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_JUSTIFY
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import mm
        from reportlab.platypus import (
            HRFlowable,
            KeepTogether,
            ListFlowable,
            ListItem,
            Paragraph,
            SimpleDocTemplate,
            Spacer,
            Table,
            TableStyle,
        )
    except ImportError as exc:
        raise RuntimeError(
            "PDF generation requires the 'reportlab' package. Install it to enable downloads."
        ) from exc

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    meta = report.get("meta", {})
    patient = report.get("patient", {})
    presenting = report.get("presenting", {})

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=9.5,
        leading=13.5,
        alignment=TA_JUSTIFY,
    )
    h1 = ParagraphStyle(
        "H1", parent=styles["Heading1"], fontSize=14, leading=18, spaceAfter=2, textColor=colors.HexColor("#0f172a")
    )
    h2 = ParagraphStyle(
        "H2",
        parent=styles["Heading2"],
        fontSize=11,
        leading=15,
        spaceBefore=10,
        spaceAfter=4,
        textColor=colors.HexColor("#1d4ed8"),
    )
    small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=11, textColor=colors.HexColor("#475569"))
    warn = ParagraphStyle(
        "Warn",
        parent=body,
        fontSize=9,
        leading=12.5,
        textColor=colors.HexColor("#7f1d1d"),
        backColor=colors.HexColor("#fef2f2"),
        borderPadding=6,
        borderColor=colors.HexColor("#fecaca"),
        borderWidth=0.6,
    )
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=body,
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#374151"),
        backColor=colors.HexColor("#f8fafc"),
        borderPadding=6,
        borderColor=colors.HexColor("#cbd5e1"),
        borderWidth=0.6,
    )

    def _on_page(canvas, doc) -> None:
        """Footer with the disclaimer and page number on every page."""
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#64748b"))
        canvas.drawString(
            18 * mm,
            12 * mm,
            "For education only — not a diagnosis. Discuss with your audiologist.",
        )
        canvas.drawRightString(A4[0] - 18 * mm, 12 * mm, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=20 * mm,
        title=f"Guidance summary — {patient.get('name', 'Patient')}",
        author=meta.get("department", DEPARTMENT_NAME),
    )

    story: list[Any] = []

    story.append(Paragraph(meta.get("institute", INSTITUTE_NAME), h1))
    story.append(Paragraph(meta.get("department", DEPARTMENT_NAME), styles["Heading3"]))
    story.append(Paragraph(f"{meta.get('address', '')} &nbsp;·&nbsp; Phone: {meta.get('phone', '')}", small))
    story.append(Spacer(1, 5))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#1d4ed8"), thickness=1.2))
    story.append(Spacer(1, 8))
    story.append(Paragraph(meta.get("document_type", "Guidance summary"), h2))

    generated = meta.get("generated_at", "")
    try:
        generated = datetime.fromisoformat(generated).strftime("%d %B %Y, %I:%M %p")
    except (TypeError, ValueError):
        pass

    rows = [
        ["Name", patient.get("name", "—"), "Age", str(patient.get("age") or "—")],
        ["Gender", patient.get("gender", "—"), "District", patient.get("district", "—")],
        ["Phone", patient.get("phone") or "—", "Generated", generated or "—"],
        [
            "Concern",
            presenting.get("category") or "—",
            "Presentation",
            presenting.get("condition") or "—",
        ],
    ]
    table = Table(rows, colWidths=[24 * mm, 62 * mm, 24 * mm, 64 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                ("TEXTCOLOR", (2, 0), (2, -1), colors.HexColor("#475569")),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e2e8f0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(table)

    answers = report.get("answers") or []
    if answers:
        story.append(Paragraph("What you told us", h2))
        answer_rows = [
            [Paragraph(a.get("question", ""), body), Paragraph(f"<b>{a.get('answer', '')}</b>", body)]
            for a in answers
        ]
        answer_table = Table(answer_rows, colWidths=[112 * mm, 62 * mm])
        answer_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#e2e8f0")),
                ]
            )
        )
        story.append(answer_table)

    tests = report.get("recommended_tests") or []
    story.append(Paragraph("Suggested tests to discuss at your appointment", h2))
    if tests:
        for position, test in enumerate(tests, start=1):
            block: list[Any] = [
                Paragraph(
                    f"<b>{position}. {test.get('test_name', '')}</b>"
                    + (f" ({test.get('test_code')})" if test.get("test_code") else ""),
                    body,
                )
            ]
            if test.get("reason_text"):
                block.append(Paragraph(f"<i>Why:</i> {test['reason_text']}", body))
            if test.get("explanation"):
                block.append(Paragraph(f"<i>About this test:</i> {test['explanation']}", body))
            if test.get("preparation"):
                block.append(Paragraph(f"<i>How to prepare:</i> {test['preparation']}", body))
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))
    else:
        story.append(
            Paragraph(
                "No specific tests were identified from your answers. Please discuss your "
                "concern with the department so the right assessment can be arranged.",
                body,
            )
        )

    recommendations = report.get("general_recommendations") or []
    if recommendations:
        story.append(Paragraph("General advice", h2))
        story.append(
            ListFlowable(
                [ListItem(Paragraph(item, body), leftIndent=10) for item in recommendations],
                bulletType="bullet",
                bulletFontSize=7,
                leftIndent=12,
            )
        )

    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Urgent symptoms:</b> {report.get('urgent_notice', URGENT_NOTICE)}", warn))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Important:</b> {report.get('disclaimer', SAFETY_DISCLAIMER)}", disclaimer_style))

    doc.build(story, onFirstPage=_on_page, onLaterPages=_on_page)
    logger.info("Rendered report PDF to %s", path)
    return path


def report_filename(patient_name: str, session_id: str) -> str:
    """Filesystem-safe filename for a generated report."""
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in patient_name.strip())
    safe = (safe or "patient")[:40].strip("_")
    return f"niepmd_guidance_{safe}_{str(session_id)[:8]}.pdf"
