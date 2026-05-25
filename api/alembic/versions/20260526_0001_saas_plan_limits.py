"""add saas plan package limits

Revision ID: 20260526_0001
Revises: None
Create Date: 2026-05-26
"""
from typing import Sequence, Union

from alembic import op

revision: str = "20260526_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS plan_key VARCHAR(50) NOT NULL DEFAULT ''")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS max_transactions INTEGER DEFAULT 50")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS max_products INTEGER DEFAULT 30")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS storage_mb INTEGER DEFAULT 256")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS active_modules JSON DEFAULT '[]'")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS api_access BOOLEAN DEFAULT FALSE")
    op.execute("ALTER TABLE saas_plan ADD COLUMN IF NOT EXISTS sort_order INTEGER DEFAULT 0")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_saas_plan_plan_key "
        "ON saas_plan(plan_key) WHERE plan_key <> ''"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_saas_plan_plan_key")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS sort_order")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS api_access")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS active_modules")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS storage_mb")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS max_products")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS max_transactions")
    op.execute("ALTER TABLE saas_plan DROP COLUMN IF EXISTS plan_key")
