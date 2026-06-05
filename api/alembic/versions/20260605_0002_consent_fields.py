# gpt-5
"""add marketing consent fields to user and subscription

Revision ID: 20260605_0002
Revises: 20260605_0001
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = "20260605_0002"
down_revision = "20260605_0001"
branch_labels = None
depends_on = None


# gpt-5
def upgrade():
    op.add_column("core_users", sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("core_users", sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("saas_subscription", sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("saas_subscription", sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("core_users", "marketing_consent", server_default=None)
    op.alter_column("saas_subscription", "marketing_consent", server_default=None)


# gpt-5
def downgrade():
    op.drop_column("saas_subscription", "consent_at")
    op.drop_column("saas_subscription", "marketing_consent")
    op.drop_column("core_users", "consent_at")
    op.drop_column("core_users", "marketing_consent")
