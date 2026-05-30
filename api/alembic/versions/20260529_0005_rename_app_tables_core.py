"""rename app tables core

Revision ID: 20260529_0005
Revises: 20260529_0004
Create Date: 2026-05-29 00:00:05.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260529_0005'
down_revision = '20260529_0004'
branch_labels = None
depends_on = None

tables = {
    "erp_party_parties": "party_parties",
    "erp_party_contacts": "party_contacts",
    "erp_accounting_account_relations": "accounting_account_relations",
    "erp_accounting_accounts": "accounting_accounts",
    "erp_accounting_entries": "accounting_entries",
    "erp_accounting_entry_lines": "accounting_entry_lines",
    "erp_accounting_fiscal_periods": "accounting_fiscal_periods",
    "erp_accounting_grn_lines": "accounting_grn_lines",
    "erp_accounting_grns": "accounting_grns",
    "erp_accounting_inflow_invoice_charges": "accounting_inflow_invoice_charges",
    "erp_accounting_inflow_invoice_lines": "accounting_inflow_invoice_lines",
    "erp_accounting_inflow_invoices": "accounting_inflow_invoices",
    "erp_accounting_outflow_invoice_charges": "accounting_outflow_invoice_charges",
    "erp_accounting_outflow_invoice_lines": "accounting_outflow_invoice_lines",
    "erp_accounting_outflow_invoices": "accounting_outflow_invoices",
    "erp_accounting_payment_allocations": "accounting_payment_allocations",
    "erp_accounting_payments": "accounting_payments",
    "erp_config_charges": "config_charges",
    "erp_config_currencies": "config_currencies",
    "erp_config_exchange_rates": "config_exchange_rates",
    "erp_config_notifications": "config_notifications",
    "erp_config_org_posting_rules": "config_org_posting_rules",
    "erp_config_org_vocabulary": "config_org_vocabulary",
    "erp_config_organizations": "config_organizations",
    "erp_config_payment_accounts": "config_payment_accounts",
    "erp_config_payment_modes": "config_payment_modes",
    "erp_config_price_types": "config_price_types",
    "erp_config_print_templates": "config_print_templates",
    "erp_config_settings": "config_settings",
    "erp_config_uoms": "config_uoms",
    "erp_config_workflow_actions": "config_workflow_actions",
    "erp_config_workflow_states": "config_workflow_states",
    "erp_config_workflow_templates": "config_workflow_templates",
    "erp_config_workflow_transitions": "config_workflow_transitions",
    "erp_base": "base",
    "erp_base_saved_filters": "base_saved_filters",
    "erp_core_notes": "core_notes",
    "erp_user_access": "config_user_access",
    "erp_invoice": "invoice",
    "erp_rbac": "rbac",
    "aras_request_log": "saas_request_log"
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
