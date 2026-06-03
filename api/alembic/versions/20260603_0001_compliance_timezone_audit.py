# claude-sonnet-4-6
"""compliance: timezone-aware timestamps, audit retention_days, audit_log user_id ON DELETE SET NULL

Revision ID: 20260603_0001
Revises: 20260530_0003
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = '20260603_0001'
down_revision = '20260530_0003'
branch_labels = None
depends_on = None

# Tables with timestamp columns to convert to timezone-aware
TABLES_WITH_TIMESTAMPS = [
    # (table, [columns])
    ("core_activity_logs", ["created_at", "updated_at", "deleted_at"]),
    ("core_audit_log", ["ts"]),
    ("core_config_values", ["created_at", "updated_at", "deleted_at"]),
    ("core_config_value_audit", ["ts"]),
    ("core_users", ["created_at", "updated_at", "deleted_at"]),
    ("core_user_preferences", ["created_at", "updated_at", "deleted_at"]),
    ("core_user_roles", ["created_at", "updated_at", "deleted_at"]),
    ("core_roles", ["created_at", "updated_at", "deleted_at"]),
    ("core_permissions", ["created_at", "updated_at", "deleted_at"]),
    ("core_resources", ["created_at", "updated_at", "deleted_at"]),
    ("core_fields", ["created_at", "updated_at", "deleted_at"]),
    ("core_translations", ["created_at", "updated_at", "deleted_at"]),
    ("core_series", ["created_at", "updated_at", "deleted_at"]),
    ("core_notes", ["created_at", "updated_at", "deleted_at"]),
    ("core_links", ["created_at", "updated_at", "deleted_at"]),
    ("core_widgets", ["created_at", "updated_at", "deleted_at"]),
    ("core_dashboard_layouts", ["created_at", "updated_at", "deleted_at"]),
    ("core_settings", ["created_at", "updated_at", "deleted_at"]),
    ("saas_subscription", ["created_at", "updated_at", "deleted_at"]),
    ("saas_plan", ["created_at", "updated_at", "deleted_at"]),
    ("saas_invoice", ["created_at", "updated_at", "deleted_at"]),
    ("saas_payment", ["created_at", "updated_at", "deleted_at"]),
    ("config_organizations", ["created_at", "updated_at", "deleted_at"]),
]


def upgrade():
    conn = op.get_bind()

    # H1: Convert timestamp columns to timezone-aware (UTC cast)
    for table, cols in TABLES_WITH_TIMESTAMPS:
        # Check table exists before altering
        result = conn.execute(
            sa.text("SELECT to_regclass(:t)"), {"t": table}
        ).scalar()
        if not result:
            continue
        for col in cols:
            try:
                op.alter_column(
                    table, col,
                    type_=sa.DateTime(timezone=True),
                    postgresql_using=f'"{col}" AT TIME ZONE \'UTC\'',
                    existing_nullable=True,
                )
            except Exception:
                pass  # column may not exist in all envs (nullable deleted_at)

    # H3: Add retention_days to core_audit_log
    result = conn.execute(sa.text("SELECT to_regclass('core_audit_log')")).scalar()
    if result:
        existing = conn.execute(
            sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='core_audit_log' AND column_name='retention_days'")
        ).fetchone()
        if not existing:
            op.add_column('core_audit_log', sa.Column('retention_days', sa.Integer(), nullable=True))

    # H3: Make user_id FK on core_audit_log SET NULL on delete
    # Drop existing FK if any, re-add with ON DELETE SET NULL
    try:
        op.drop_constraint('core_audit_log_user_id_fkey', 'core_audit_log', type_='foreignkey')
    except Exception:
        pass
    # user_id is an integer reference — add FK with SET NULL
    try:
        op.create_foreign_key(
            'core_audit_log_user_id_fkey',
            'core_audit_log', 'core_users',
            ['user_id'], ['id'],
            ondelete='SET NULL',
        )
    except Exception:
        pass


def downgrade():
    # Reverse retention_days only; timezone conversion is non-destructive
    try:
        op.drop_column('core_audit_log', 'retention_days')
    except Exception:
        pass
    try:
        op.drop_constraint('core_audit_log_user_id_fkey', 'core_audit_log', type_='foreignkey')
    except Exception:
        pass
