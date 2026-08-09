"""Assistant suite: services, scheduling, knowledge base, guidance, conversations.

Revision ID: 002_assistant_suite
Revises: 001_initial
Create Date: 2026-07-31
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_assistant_suite"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(60), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("vertical", sa.String(40), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("preparation", sa.Text(), nullable=True),
        sa.Column("documents_required", postgresql.JSONB(), nullable=True),
        sa.Column("report_turnaround", sa.String(120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("code", name="uq_services_code"),
    )
    op.create_index("ix_services_code", "services", ["code"])
    op.create_index("ix_services_vertical", "services", ["vertical"])

    op.create_table(
        "clinicians",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("designation", sa.String(120), nullable=False),
        sa.Column("vertical", sa.String(40), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_index("ix_clinicians_vertical", "clinicians", ["vertical"])

    op.create_table(
        "appointment_slots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("clinician_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("booked_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(40), nullable=False, server_default="open"),
        sa.Column("location", sa.String(200), nullable=True),
        sa.Column("external_ref", sa.String(120), nullable=True),
        sa.ForeignKeyConstraint(["service_id"], ["services.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["clinician_id"], ["clinicians.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_appointment_slots_service_id", "appointment_slots", ["service_id"])
    op.create_index("ix_appointment_slots_clinician_id", "appointment_slots", ["clinician_id"])
    op.create_index("ix_appointment_slots_starts_at", "appointment_slots", ["starts_at"])
    op.create_index("ix_appointment_slots_external_ref", "appointment_slots", ["external_ref"])

    op.create_table(
        "agent_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_type", sa.String(40), nullable=False),
        sa.Column("vertical", sa.String(40), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="active"),
        sa.Column("context", postgresql.JSONB(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_agent_conversations_agent_type", "agent_conversations", ["agent_type"])
    op.create_index("ix_agent_conversations_vertical", "agent_conversations", ["vertical"])
    op.create_index("ix_agent_conversations_session_id", "agent_conversations", ["session_id"])
    op.create_index("ix_agent_conversations_status", "agent_conversations", ["status"])

    op.create_table(
        "agent_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True),
        sa.Column("sources", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_agent_messages_conversation_id", "agent_messages", ["conversation_id"])

    op.create_table(
        "appointments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_code", sa.String(20), nullable=False),
        sa.Column("slot_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("patient_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(30), nullable=False),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("status", sa.String(40), nullable=False, server_default="requested"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("external_ref", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["slot_id"], ["appointment_slots.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("reference_code", name="uq_appointments_reference_code"),
    )
    op.create_index("ix_appointments_reference_code", "appointments", ["reference_code"])
    op.create_index("ix_appointments_slot_id", "appointments", ["slot_id"])
    op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
    op.create_index("ix_appointments_status", "appointments", ["status"])

    op.create_table(
        "knowledge_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("vertical", sa.String(40), nullable=False),
        sa.Column("agent_types", postgresql.JSONB(), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("slug", name="uq_knowledge_entries_slug"),
    )
    op.create_index("ix_knowledge_entries_slug", "knowledge_entries", ["slug"])
    op.create_index("ix_knowledge_entries_vertical", "knowledge_entries", ["vertical"])

    op.create_table(
        "screening_protocols",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("age_band", sa.String(40), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("test_codes", postgresql.JSONB(), nullable=False),
        sa.Column("referral_criteria", postgresql.JSONB(), nullable=False),
        sa.Column("timeline", sa.Text(), nullable=False),
        sa.Column("preparation", sa.Text(), nullable=True),
        sa.UniqueConstraint("age_band", name="uq_screening_protocol_age_band"),
    )
    op.create_index("ix_screening_protocols_age_band", "screening_protocols", ["age_band"])

    op.create_table(
        "therapy_guidelines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("domain", sa.String(60), nullable=False),
        sa.Column("age_band", sa.String(40), nullable=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("milestones", postgresql.JSONB(), nullable=False),
        sa.Column("home_activities", postgresql.JSONB(), nullable=False),
        sa.Column("red_flags", postgresql.JSONB(), nullable=False),
        sa.Column("typical_frequency", sa.String(200), nullable=True),
        sa.UniqueConstraint("domain", "age_band", name="uq_therapy_guideline_domain_age"),
    )
    op.create_index("ix_therapy_guidelines_domain", "therapy_guidelines", ["domain"])
    op.create_index("ix_therapy_guidelines_age_band", "therapy_guidelines", ["age_band"])

    op.create_table(
        "counselling_resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(120), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False),
        sa.Column("age_band", sa.String(40), nullable=True),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("talking_points", postgresql.JSONB(), nullable=False),
        sa.Column("reassurance", postgresql.JSONB(), nullable=False),
        sa.Column("next_steps", postgresql.JSONB(), nullable=False),
        sa.Column("keywords", postgresql.JSONB(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_counselling_resources_slug"),
    )
    op.create_index("ix_counselling_resources_slug", "counselling_resources", ["slug"])
    op.create_index("ix_counselling_resources_age_band", "counselling_resources", ["age_band"])

    op.create_table(
        "escalation_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("reference_code", sa.String(20), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("agent_type", sa.String(40), nullable=False),
        sa.Column("vertical", sa.String(40), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(20), nullable=False, server_default="routine"),
        sa.Column("status", sa.String(20), nullable=False, server_default="open"),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_phone", sa.String(30), nullable=True),
        sa.Column("triggers", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["agent_conversations.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint("reference_code", name="uq_escalation_tickets_reference_code"),
    )
    op.create_index("ix_escalation_tickets_reference_code", "escalation_tickets", ["reference_code"])
    op.create_index("ix_escalation_tickets_vertical", "escalation_tickets", ["vertical"])
    op.create_index("ix_escalation_tickets_priority", "escalation_tickets", ["priority"])
    op.create_index("ix_escalation_tickets_status", "escalation_tickets", ["status"])


def downgrade() -> None:
    op.drop_table("escalation_tickets")
    op.drop_table("counselling_resources")
    op.drop_table("therapy_guidelines")
    op.drop_table("screening_protocols")
    op.drop_table("knowledge_entries")
    op.drop_table("appointments")
    op.drop_table("agent_messages")
    op.drop_table("agent_conversations")
    op.drop_table("appointment_slots")
    op.drop_table("clinicians")
    op.drop_table("services")
