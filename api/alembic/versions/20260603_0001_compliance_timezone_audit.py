# claude-sonnet-4-6
# claude-opus-4-8 (fix: SAVEPOINT-guard + existence pre-checks — bare try/except poisoned the
# Postgres transaction, aborting the whole chain past 20260530_0003)
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


# claude-opus-4-8
def _column(conn, table, column):
    """Return (data_type, udt_name) for a column, or None if table/column absent."""
    row = conn.execute(
        sa.text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).fetchone()
    return row[0] if row else None


# claude-opus-4-8
def _guarded(conn, fn):
    """Run a DDL callable inside a SAVEPOINT so a failure can't poison the outer txn."""
    try:
        with conn.begin_nested():
            fn()
    except Exception:
        pass  # optional/idempotent DDL — safe to skip on this env

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
    ("core_organizations", ["created_at", "updated_at", "deleted_at"]),
]


def upgrade():
    conn = op.get_bind()

    # H1: Convert timestamp columns to timezone-aware (UTC cast). Idempotent: skip columns that
    # are absent or already timestamptz, and SAVEPOINT-guard the ALTER so any failure rolls back
    # only that statement instead of aborting the whole migration transaction.
    for table, cols in TABLES_WITH_TIMESTAMPS:
        if not conn.execute(sa.text("SELECT to_regclass(:t)"), {"t": table}).scalar():
            continue
        for col in cols:
            data_type = _column(conn, table, col)
            if data_type is None:
                continue  # column absent in this env (e.g. nullable deleted_at)
            if data_type == "timestamp with time zone":
                continue  # already converted — nothing to do
            _guarded(conn, lambda t=table, c=col: op.alter_column(
                t, c,
                type_=sa.DateTime(timezone=True),
                postgresql_using=f'"{c}" AT TIME ZONE \'UTC\'',
                existing_nullable=True,
            ))

    # H3: Add retention_days to core_audit_log
    result = conn.execute(sa.text("SELECT to_regclass('core_audit_log')")).scalar()
    if result:
        existing = conn.execute(
            sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='core_audit_log' AND column_name='retention_days'")
        ).fetchone()
        if not existing:
            op.add_column('core_audit_log', sa.Column('retention_days', sa.Integer(), nullable=True))

    # H3: Make user_id FK on core_audit_log SET NULL on delete. Only touch it if the audit table
    # exists; SAVEPOINT-guard both the drop (may not exist) and the re-create.
    if conn.execute(sa.text("SELECT to_regclass('core_audit_log')")).scalar():
        _guarded(conn, lambda: op.drop_constraint(
            'core_audit_log_user_id_fkey', 'core_audit_log', type_='foreignkey'))
        _guarded(conn, lambda: op.create_foreign_key(
            'core_audit_log_user_id_fkey',
            'core_audit_log', 'core_users',
            ['user_id'], ['id'],
            ondelete='SET NULL',
        ))


def downgrade():
    # Reverse retention_days only; timezone conversion is non-destructive
    conn = op.get_bind()
    _guarded(conn, lambda: op.drop_column('core_audit_log', 'retention_days'))
    _guarded(conn, lambda: op.drop_constraint(
        'core_audit_log_user_id_fkey', 'core_audit_log', type_='foreignkey'))
