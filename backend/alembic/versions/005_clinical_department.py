"""Add clinical department (Audiology vs Speech Language) to profiles and categories.

Patients choose a department at registration; concern categories are filtered to
that department on the next step.

Revision ID: 005_clinical_department
Revises: 004_test_catalog_detail
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "005_clinical_department"
down_revision = "004_test_catalog_detail"
branch_labels = None
depends_on = None

_SPEECH_SLUGS = ("speech-voice-adult", "child-speech-delay")


def upgrade() -> None:
    op.add_column(
        "patient_profiles",
        sa.Column("department", sa.String(length=40), nullable=True),
    )
    op.create_index("ix_patient_profiles_department", "patient_profiles", ["department"])

    op.add_column(
        "treatment_categories",
        sa.Column("department", sa.String(length=40), nullable=True),
    )
    op.create_index("ix_treatment_categories_department", "treatment_categories", ["department"])

    conn = op.get_bind()
    speech_list = ", ".join(f"'{s}'" for s in _SPEECH_SLUGS)
    conn.execute(
        sa.text(
            f"UPDATE treatment_categories SET department = 'speech_language' "
            f"WHERE slug IN ({speech_list})"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE treatment_categories SET department = 'audiology' "
            "WHERE department IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_treatment_categories_department", table_name="treatment_categories")
    op.drop_column("treatment_categories", "department")
    op.drop_index("ix_patient_profiles_department", table_name="patient_profiles")
    op.drop_column("patient_profiles", "department")
