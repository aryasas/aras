"""rename app tables mid

Revision ID: 20260529_0004
Revises: 20260529_0003
Create Date: 2026-05-29 00:00:04.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260529_0004'
down_revision = '20260529_0003'
branch_labels = None
depends_on = None

tables = {
    "erp_stock_categories": "stock_categories",
    "erp_stock_items": "stock_items",
    "erp_stock_item_accounts": "stock_item_accounts",
    "erp_stock_item_uoms": "stock_item_uoms",
    "erp_stock_pricelists": "stock_pricelists",
    "erp_stock_promo_bundles": "stock_promo_bundles",
    "erp_stock_promo_items": "stock_promo_items",
    "erp_stock_locations": "stock_locations",
    "erp_stock_delivery_notes": "stock_delivery_notes",
    "erp_stock_delivery_note_lines": "stock_delivery_note_lines",
    "erp_stock_movements": "stock_movements",
    "erp_stock_movement_lines": "stock_movement_lines",
    "erp_stock_item_bundles": "stock_item_bundles",
    "erp_stock_item_locations": "stock_item_locations",
    "erp_crm_pipelines": "crm_pipelines",
    "erp_crm_stages": "crm_stages",
    "erp_crm_leads": "crm_leads",
    "erp_crm_activities": "crm_activities",
    "erp_pot_terminals": "pot_terminals",
    "erp_pot_sessions": "pot_sessions",
    "erp_report_reports": "report_reports"
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
