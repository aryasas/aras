"""drop_stale_tables

Removes orphan tables left behind by prior renames/migrations:
- config_settings (empty; superseded by core_settings)
- core_sys_settings (8 rows already migrated to core_settings by 20260530_0001)
- user_access (1 row already mirrored in core_user_access)

Revision ID: 20260530_0003
Revises: 20260530_0002
Create Date: 2026-05-30 17:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '20260530_0003'
down_revision = '20260530_0002'
branch_labels = None
depends_on = None


STALE_TABLES = ['config_settings', 'core_sys_settings', 'user_access']


def upgrade():
    bind = op.get_bind()
    existing = set(sa.inspect(bind).get_table_names())
    for t in STALE_TABLES:
        if t in existing:
            op.execute(f'DROP TABLE "{t}" CASCADE')


def downgrade():
    # Stale tables intentionally not recreated.
    pass
