"""
Sprint POT-mode DB migration — idempotent:
- stock_product: add account_revenue_id, account_purchase_id, account_cogs_id
- pos_terminal: add transaction_mode
- core_setting: add erp.accounting_mode_hpp + COA default settings
"""
from arasCore.lib.core.extensions import db


def _col_exists(table, col):
    return db.session.execute(db.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema=DATABASE() AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": col}).scalar() > 0


def _add_col(table, col, definition):
    if not _col_exists(table, col):
        db.session.execute(db.text(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {definition}"))
        db.session.commit()


def _setting_exists(key):
    return db.session.execute(db.text(
        "SELECT COUNT(*) FROM setting WHERE scope='global' AND `key`=:k"
    ), {"k": key}).scalar() > 0


def run(app):
    with app.app_context():
        _add_col("stock_product", "account_revenue_id",  "BIGINT NULL")
        _add_col("stock_product", "account_purchase_id", "BIGINT NULL")
        _add_col("stock_product", "account_cogs_id",     "BIGINT NULL")
        _add_col("pos_terminal", "transaction_mode",
                 "ENUM('income','outcome','both') NOT NULL DEFAULT 'income'")

        for key, vtype, value in [
            ("erp.accounting_mode_hpp",      "bool", "false"),
            ("erp.account_revenue_default",  "int",  "0"),
            ("erp.account_purchase_default", "int",  "0"),
            ("erp.account_cogs_default",     "int",  "0"),
        ]:
            if not _setting_exists(key):
                db.session.execute(db.text(
                    "INSERT INTO setting (scope, scope_id, `key`, value_type, value) "
                    "VALUES ('global', NULL, :k, :vt, :v)"
                ), {"k": key, "vt": vtype, "v": value})
        db.session.commit()
        print("[migrate_task6] done.")
