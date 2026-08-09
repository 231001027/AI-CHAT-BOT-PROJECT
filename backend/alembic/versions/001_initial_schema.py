"""Initial schema + seed ConcernConfig / TestCatalog.

Revision ID: 001_initial
Revises:
Create Date: 2026-07-30
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("district", sa.String(120), nullable=False),
        sa.Column("age", sa.Integer(), nullable=False),
        sa.Column("gender", sa.String(40), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("user_type", sa.String(40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "concern_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concern_type", sa.String(60), nullable=False),
        sa.Column("age_band", sa.String(40), nullable=True),
        sa.Column("common_signs", postgresql.JSONB(), nullable=False),
        sa.Column("recommended_tests", postgresql.JSONB(), nullable=False),
        sa.Column("what_it_helps", sa.Text(), nullable=False),
        sa.Column("outcome_options", postgresql.JSONB(), nullable=True),
        sa.Column("conditional_rules", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_concern_configs_concern_type", "concern_configs", ["concern_type"])
    op.create_index("ix_concern_configs_age_band", "concern_configs", ["age_band"])

    op.create_table(
        "test_catalog",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(40), nullable=False, unique=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(60), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
    )
    op.create_index("ix_test_catalog_code", "test_catalog", ["code"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chat_history", postgresql.JSONB(), nullable=False),
        sa.Column("current_step", sa.String(40), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("context", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_chat_sessions_patient_id", "chat_sessions", ["patient_id"])

    op.create_table(
        "concerns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False),
        sa.Column("concern_type", sa.String(60), nullable=False),
        sa.Column("source_page", sa.String(40), nullable=False),
        sa.Column("age_band", sa.String(40), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_concerns_patient_id", "concerns", ["patient_id"])
    op.create_index("ix_concerns_concern_type", "concerns", ["concern_type"])

    op.create_table(
        "symptom_responses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("concern_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("concerns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_key", sa.String(80), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_symptom_responses_concern_id", "symptom_responses", ["concern_id"])

    op.create_table(
        "booking_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("patients.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("preferred_slot", sa.String(120), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("booking_requests")
    op.drop_table("symptom_responses")
    op.drop_table("concerns")
    op.drop_table("chat_sessions")
    op.drop_index("ix_test_catalog_code", table_name="test_catalog")
    op.drop_table("test_catalog")
    op.drop_index("ix_concern_configs_age_band", table_name="concern_configs")
    op.drop_index("ix_concern_configs_concern_type", table_name="concern_configs")
    op.drop_table("concern_configs")
    op.drop_table("patients")
