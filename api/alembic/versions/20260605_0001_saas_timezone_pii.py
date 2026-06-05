# gpt-5
"""saas: timezone-aware timestamps for SaaS app tables

Revision ID: 20260605_0001
Revises: 20260603_0001
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260605_0001"
down_revision = "20260603_0001"
branch_labels = None
depends_on = None

SAAS_TIMESTAMP_COLUMNS = [
    ("saas_subscription", "started_at"),
    ("saas_subscription", "expires_at"),
    ("saas_subscription", "next_billing_at"),
    ("saas_subscription", "trial_ends_at"),
    ("saas_license_token", "issued_at"),
    ("saas_license_token", "expires_at"),
    ("saas_activation_request", "requested_at"),
    ("saas_invoice", "period_start"),
    ("saas_invoice", "period_end"),
    ("saas_invoice", "due_at"),
    ("saas_invoice", "paid_at"),
    ("saas_request_log", "ts"),
]


# gpt-5
def upgrade():
    for table, col in SAAS_TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            col,
            type_=sa.DateTime(timezone=True),
            postgresql_using=f'"{col}" AT TIME ZONE \'UTC\'',
            existing_nullable=True,
        )


# gpt-5
def downgrade():
    for table, col in SAAS_TIMESTAMP_COLUMNS:
        op.alter_column(
            table,
            col,
            type_=sa.DateTime(),
            existing_nullable=True,
        )
