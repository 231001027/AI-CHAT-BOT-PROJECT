"""Add preparation guidance and duration to the test catalogue.

Preparation instructions are deterministic, department-owned content. Storing
them here keeps "how to prepare" and "how long it takes" out of the language
model's reach, where a plausible-sounding invention could send a patient to an
appointment unprepared.

Revision ID: 004_test_catalog_detail
Revises: 003_clinical_core
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "004_test_catalog_detail"
down_revision = "003_clinical_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("test_catalog", sa.Column("preparation", sa.Text(), nullable=True))
    op.add_column("test_catalog", sa.Column("duration_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("test_catalog", "duration_minutes")
    op.drop_column("test_catalog", "preparation")
