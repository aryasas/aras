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


# claude-opus-4-8
def _has_column(conn, table, column):
    return conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone() is not None


# gpt-5
# claude-opus-4-8 (idempotent: columns may already exist via auto_migrate before this ran)
def upgrade():
    conn = op.get_bind()
    for table in ("core_users", "saas_subscription"):
        if not _has_column(conn, table, "marketing_consent"):
            op.add_column(table, sa.Column("marketing_consent", sa.Boolean(), nullable=False, server_default=sa.false()))
            op.alter_column(table, "marketing_consent", server_default=None)
        if not _has_column(conn, table, "consent_at"):
            op.add_column(table, sa.Column("consent_at", sa.DateTime(timezone=True), nullable=True))


# gpt-5
# claude-opus-4-8 (guarded drops)
def downgrade():
    conn = op.get_bind()
    for table in ("saas_subscription", "core_users"):
        if _has_column(conn, table, "consent_at"):
            op.drop_column(table, "consent_at")
        if _has_column(conn, table, "marketing_consent"):
            op.drop_column(table, "marketing_consent")
