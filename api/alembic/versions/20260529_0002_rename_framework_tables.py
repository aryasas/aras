"""rename framework tables

Revision ID: 20260529_0002
Revises: 20260529_0001
Create Date: 2026-05-29 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260529_0002'
down_revision = '20260529_0001'
branch_labels = None
depends_on = None

tables = {
    "aras_apps": "core_apps",
    "auth_users": "core_users",
    "auth_roles": "core_roles",
    "auth_user_roles": "core_user_roles",
    "auth_permissions": "core_permissions",
    "auth_user_preferences": "core_user_preferences",
    "aras_fields": "core_fields",
    "aras_links": "core_links",
    "aras_resources": "core_resources",
    "aras_widgets": "core_widgets",
    "translations": "core_translations",
    "aras_dashboard_layouts": "core_dashboard_layouts",
    "aras_activity_logs": "core_activity_logs",
    "doc_series": "core_series",
    "sys_settings": "core_sys_settings",
    "config_values": "core_config_values",
    "config_value_audit": "core_config_value_audit",
    "audit_log": "core_audit_log",
    "numbering_sequences": "core_numbering_sequences"
}

def upgrade() -> None:
    from sqlalchemy import inspect
    insp = inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for old_t, new_t in tables.items():
        if old_t not in existing:
            continue
        if new_t in existing:
            # auto_migrate might have prematurely created the new table empty. Drop it so we can rename the old one (which has data).
            op.execute(f"DROP TABLE {new_t} CASCADE")
        op.rename_table(old_t, new_t)
        op.execute(f"ALTER INDEX IF EXISTS ix_{old_t}_id RENAME TO ix_{new_t}_id")

def downgrade() -> None:
    from sqlalchemy import inspect
    insp = inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for old_t, new_t in tables.items():
        if new_t not in existing:
            continue
        op.rename_table(new_t, old_t)
        op.execute(f"ALTER INDEX IF EXISTS ix_{new_t}_id RENAME TO ix_{old_t}_id")
