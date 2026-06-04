# claude-sonnet-4-6
"""
Phase 2 keystone migration: move per-org accounting/stock defaults off Organization.

The 14 acc_* defaults + COA/charge fields move to accounting.AccountingConfig;
inventory flags + 5 stock accounts move to stock.StockConfig. Both are registered
via App.config_model and read by key through AppConfigRegistry — so the framework
(and a free plan without accounting/stock) never depends on these columns.

This migration:
  1. Creates accounting_config + stock_config tables from the live model metadata.
  2. Drops the 27 now-orphaned columns from core_organizations.

Idempotent: CREATE ... IF NOT EXISTS via checkfirst; DROP COLUMN IF EXISTS.
Authorized to drop data (dev DB) — these columns were never the source of truth
once the config tables exist.

Run: python -m core.migrations.move_acc_to_app_config
"""
from sqlalchemy import text
from core.lib.database import engine
import importlib

# Columns to remove from core_organizations (now owned by AccountingConfig/StockConfig)
_ORG_DROP_COLUMNS = [
    # accounting defaults
    "acc_bank_default_id", "acc_cash_default_id", "acc_receivable_default_id",
    "acc_payable_default_id", "acc_income_default_id", "acc_cogs_default_id",
    "acc_inventory_default_id", "acc_payroll_payable_id", "acc_payment_discount_id",
    "acc_write_off_id", "acc_unrealized_gain_loss_id", "acc_round_off_id",
    "acc_tax_output_ppn_id", "acc_tax_input_ppn_id",
    "default_coa_template", "default_charge_id", "default_charge_enable",
    # stock config
    "acc_stock_received_not_billed_id", "acc_stock_provisional_id",
    "acc_stock_adjustment_id", "acc_expenses_in_valuation_id", "acc_stock_default_id",
    "enable_perpetual_inventory", "enable_provisional_non_stock",
    "avg_cost_by_location", "allow_zero_stock", "stock_valuation_method",
]


# claude-sonnet-4-6
def run():
    # 1. Create the new config tables from live model metadata.
    #    Importing main fully initializes the app registry so Mapped[] FK column
    #    types are resolved (bare config_models import leaves NullType at DDL time).
    import main  # noqa: F401 — side effect: load + configure all mappers
    AccountingConfig = importlib.import_module("apps.accounting.config_models").AccountingConfig
    StockConfig = importlib.import_module("apps.stock.config_models").StockConfig

    AccountingConfig.__table__.create(bind=engine, checkfirst=True)
    StockConfig.__table__.create(bind=engine, checkfirst=True)

    # 2. Drop orphaned columns from core_organizations.
    with engine.begin() as conn:
        for col in _ORG_DROP_COLUMNS:
            conn.execute(text(
                f'ALTER TABLE core_organizations DROP COLUMN IF EXISTS "{col}"'
            ))

    print(f"Created accounting_config, stock_config; "
          f"dropped {len(_ORG_DROP_COLUMNS)} columns from core_organizations.")


if __name__ == "__main__":
    run()
