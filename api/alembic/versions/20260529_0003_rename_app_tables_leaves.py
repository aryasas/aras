"""rename app tables leaves

Revision ID: 20260529_0003
Revises: 20260529_0002
Create Date: 2026-05-29 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260529_0003'
down_revision = '20260529_0002'
branch_labels = None
depends_on = None

tables = {
    "erp_ticket_teams": "ticket_teams",
    "erp_ticket_categories": "ticket_categories",
    "erp_ticket_tickets": "ticket_tickets",
    "erp_ticket_messages": "ticket_messages",
    "erp_hr_departments": "hr_departments",
    "erp_hr_positions": "hr_positions",
    "erp_hr_employees": "hr_employees",
    "erp_asset_categories": "accounting_assets_categories",
    "erp_asset_assets": "accounting_assets_assets"
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
    
    op.execute("DELETE FROM core_apps WHERE name='asset'")

def downgrade() -> None:
    from sqlalchemy import inspect
    insp = inspect(op.get_bind())
    existing = set(insp.get_table_names())
    for old_t, new_t in tables.items():
        if new_t not in existing:
            continue
        op.rename_table(new_t, old_t)
        op.execute(f"ALTER INDEX IF EXISTS ix_{new_t}_id RENAME TO ix_{old_t}_id")
