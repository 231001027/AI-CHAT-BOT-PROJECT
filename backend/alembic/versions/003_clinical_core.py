"""Clinical core: profiles, staff, question bank, rules, plans, reports, RAG corpus.

Revision ID: 003_clinical_core
Revises: 002_assistant_suite
Create Date: 2026-07-31
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_clinical_core"
down_revision: Union[str, None] = "002_assistant_suite"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("specialization", sa.String(120), nullable=True),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("role", sa.String(40), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_doctors_email"),
    )
    op.create_index("ix_doctors_email", "doctors", ["email"])
    op.create_index("ix_doctors_role", "doctors", ["role"])

    op.create_table(
        "patient_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("flow_type", sa.String(20), nullable=False),
        sa.Column("child_subtype", sa.String(40), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("consent_by", sa.String(200), nullable=True),
        sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_patient_profiles_patient_id", "patient_profiles", ["patient_id"])

    op.create_table(
        "treatment_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("flow_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("slug", name="uq_treatment_categories_slug"),
    )
    op.create_index("ix_treatment_categories_slug", "treatment_categories", ["slug"])
    op.create_index("ix_treatment_categories_flow_type", "treatment_categories", ["flow_type"])

    op.create_table(
        "conditions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["category_id"], ["treatment_categories.id"], ondelete="CASCADE"
        ),
        sa.UniqueConstraint("slug", name="uq_conditions_slug"),
    )
    op.create_index("ix_conditions_slug", "conditions", ["slug"])
    op.create_index("ix_conditions_category_id", "conditions", ["category_id"])

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("condition_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key", sa.String(80), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "question_type", sa.String(30), nullable=False, server_default="single_select"
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_entry", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["condition_id"], ["conditions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_questions_key", "questions", ["key"])
    # Serves the ordered per-condition question fetch on the patient path.
    op.create_index(
        "ix_questions_condition_order", "questions", ["condition_id", "display_order"]
    )

    op.create_table(
        "question_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(300), nullable=False),
        sa.Column("value", sa.String(80), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_terminal", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["next_question_id"], ["questions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_question_options_question_id", "question_options", ["question_id"])

    op.create_table(
        "questionnaire_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("condition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="active"),
        sa.Column("current_question_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["category_id"], ["treatment_categories.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["condition_id"], ["conditions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["current_question_id"], ["questions.id"], ondelete="SET NULL"),
    )
    op.create_index(
        "ix_questionnaire_sessions_patient_id", "questionnaire_sessions", ["patient_id"]
    )
    op.create_index(
        "ix_questionnaire_sessions_condition_id", "questionnaire_sessions", ["condition_id"]
    )
    op.create_index("ix_questionnaire_sessions_status", "questionnaire_sessions", ["status"])

    op.create_table(
        "patient_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("selected_option_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("question_key", sa.String(80), nullable=False),
        sa.Column("answer_value", sa.String(200), nullable=False),
        sa.Column("answer_label", sa.Text(), nullable=False, server_default=""),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["session_id"], ["questionnaire_sessions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["selected_option_id"], ["question_options.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "session_id", "question_id", name="uq_patient_answer_session_question"
        ),
    )
    op.create_index("ix_patient_answers_session_id", "patient_answers", ["session_id"])
    op.create_index("ix_patient_answers_patient_id", "patient_answers", ["patient_id"])

    op.create_table(
        "clinical_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("condition_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("rule_definition", postgresql.JSONB(), nullable=False),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(
            ["category_id"], ["treatment_categories.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["condition_id"], ["conditions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_clinical_rules_condition_id", "clinical_rules", ["condition_id"])
    # GIN index for querying inside the rule predicate.
    op.create_index(
        "ix_clinical_rules_definition",
        "clinical_rules",
        ["rule_definition"],
        postgresql_using="gin",
    )

    op.create_table(
        "recommended_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("rule_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_code", sa.String(60), nullable=False),
        sa.Column("test_name", sa.String(200), nullable=False),
        sa.Column("reason_text", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["rule_id"], ["clinical_rules.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_recommended_tests_rule_id", "recommended_tests", ["rule_id"])

    op.create_table(
        "treatment_plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommended_tests", postgresql.JSONB(), nullable=False),
        sa.Column("matched_rule_ids", postgresql.JSONB(), nullable=False),
        sa.Column("general_recommendations", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["questionnaire_sessions.id"], ondelete="CASCADE"
        ),
    )
    op.create_index("ix_treatment_plans_patient_id", "treatment_plans", ["patient_id"])
    op.create_index("ix_treatment_plans_session_id", "treatment_plans", ["session_id"])

    op.create_table(
        "medical_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("report_json", postgresql.JSONB(), nullable=False),
        sa.Column("pdf_path", sa.String(500), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["questionnaire_sessions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["plan_id"], ["treatment_plans.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_medical_reports_patient_id", "medical_reports", ["patient_id"])
    op.create_index("ix_medical_reports_session_id", "medical_reports", ["session_id"])

    op.create_table(
        "hospital_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("category", sa.String(40), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(300), nullable=True),
        sa.Column("content_type", sa.String(120), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("test_tags", postgresql.JSONB(), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="uploaded"),
        sa.Column("vector_indexed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("index_error", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["uploaded_by"], ["doctors.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_hospital_documents_category", "hospital_documents", ["category"])
    op.create_index("ix_hospital_documents_status", "hospital_documents", ["status"])

    op.create_table(
        "ai_conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("patient_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("recommended_test_name", sa.String(200), nullable=False),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("prompt_context", postgresql.JSONB(), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("source", sa.String(30), nullable=False, server_default="rag"),
        sa.Column("model", sa.String(120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["patient_id"], ["patients.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(
            ["session_id"], ["questionnaire_sessions.id"], ondelete="SET NULL"
        ),
    )
    op.create_index("ix_ai_conversations_patient_id", "ai_conversations", ["patient_id"])
    op.create_index("ix_ai_conversations_session_id", "ai_conversations", ["session_id"])
    op.create_index("ix_ai_conversations_test_name", "ai_conversations", ["recommended_test_name"])
    op.create_index("ix_ai_conversations_source", "ai_conversations", ["source"])

    op.create_table(
        "static_explanations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("test_code", sa.String(60), nullable=False),
        sa.Column("test_name", sa.String(200), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("test_code", name="uq_static_explanations_test_code"),
    )
    op.create_index("ix_static_explanations_test_code", "static_explanations", ["test_code"])

    # Appointments raised from the clinical flow name a doctor and time directly,
    # rather than selecting a pre-generated slot.
    op.add_column(
        "appointments",
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "appointments",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_appointments_doctor_id",
        "appointments",
        "doctors",
        ["doctor_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])


def downgrade() -> None:
    op.drop_index("ix_appointments_doctor_id", table_name="appointments")
    op.drop_constraint("fk_appointments_doctor_id", "appointments", type_="foreignkey")
    op.drop_column("appointments", "scheduled_at")
    op.drop_column("appointments", "doctor_id")

    op.drop_table("static_explanations")
    op.drop_table("ai_conversations")
    op.drop_table("hospital_documents")
    op.drop_table("medical_reports")
    op.drop_table("treatment_plans")
    op.drop_table("recommended_tests")
    op.drop_table("clinical_rules")
    op.drop_table("patient_answers")
    op.drop_table("questionnaire_sessions")
    op.drop_table("question_options")
    op.drop_table("questions")
    op.drop_table("conditions")
    op.drop_table("treatment_categories")
    op.drop_table("patient_profiles")
    op.drop_table("doctors")
