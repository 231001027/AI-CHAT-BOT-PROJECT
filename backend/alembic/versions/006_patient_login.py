"""Add patient portal credentials: user_code (e.g. 123/2026) and date_of_birth.

Revision ID: 006_patient_login
Revises: 005_clinical_department
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "006_patient_login"
down_revision = "005_clinical_department"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("patients", sa.Column("user_code", sa.String(length=40), nullable=True))
    op.add_column("patients", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.create_index("ix_patients_user_code", "patients", ["user_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_patients_user_code", table_name="patients")
    op.drop_column("patients", "date_of_birth")
    op.drop_column("patients", "user_code")
