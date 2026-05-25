"""add safe report execution fields

Revision ID: 20260526_0002
Revises: 20260526_0001
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260526_0002"
down_revision: Union[str, None] = "20260526_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE erp_report_reports ADD COLUMN IF NOT EXISTS query_filters JSON")
    op.execute("ALTER TABLE erp_report_reports ADD COLUMN IF NOT EXISTS linked_doctype VARCHAR(100)")
    op.execute("ALTER TABLE erp_report_reports ADD COLUMN IF NOT EXISTS script TEXT")
    op.execute(
        "UPDATE erp_report_reports "
        "SET report_type = 'builtin' "
        "WHERE report_type NOT IN ('builtin', 'orm')"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE erp_report_reports DROP COLUMN IF EXISTS linked_doctype")
    op.execute("ALTER TABLE erp_report_reports DROP COLUMN IF EXISTS query_filters")
