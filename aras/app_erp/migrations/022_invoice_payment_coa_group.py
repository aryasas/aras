"""
022 — add acc_invoice_payment, acc_account.is_group,
      drop amount_paid/amount_due from invoices,
      drop stock_product: product_type, barcode, cost_price, standard_price
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.extensions import db
    with flask_app.app_context():
        insp   = inspect(db.engine)
        tables = insp.get_table_names()

        if "acc_invoice_payment" not in tables:
            db.session.execute(text("""
                CREATE TABLE acc_invoice_payment (
                    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
                    sales_invoice_id    BIGINT,
                    purchase_invoice_id BIGINT,
                    payment_date        DATE NOT NULL,
                    method              VARCHAR(50) NOT NULL DEFAULT 'cash',
                    amount              NUMERIC(18,4) NOT NULL,
                    reference           VARCHAR(100),
                    notes               TEXT,
                    journal_entry_id    BIGINT,
                    is_active           TINYINT(1) NOT NULL DEFAULT 1,
                    created_at          DATETIME DEFAULT NOW(),
                    updated_at          DATETIME DEFAULT NOW(),
                    created_by_id       INTEGER,
                    updated_by_id       INTEGER
                )
            """))
            logger.info("[022] acc_invoice_payment created")
        else:
            pay_cols = {c["name"] for c in insp.get_columns("acc_invoice_payment")}
            for col in ("company_id", "doc_type", "invoice_id", "mode_of_payment_id"):
                if col in pay_cols:
                    db.session.execute(text(f"ALTER TABLE acc_invoice_payment DROP COLUMN {col}"))
            for col, defn in (
                ("sales_invoice_id",    "BIGINT"),
                ("purchase_invoice_id", "BIGINT"),
                ("method",              "VARCHAR(50) NOT NULL DEFAULT 'cash'"),
                ("notes",               "TEXT"),
            ):
                if col not in pay_cols:
                    db.session.execute(text(f"ALTER TABLE acc_invoice_payment ADD COLUMN {col} {defn}"))

        acc_cols = {c["name"] for c in insp.get_columns("acc_account")}
        if "is_group" not in acc_cols:
            db.session.execute(text(
                "ALTER TABLE acc_account ADD COLUMN is_group TINYINT(1) NOT NULL DEFAULT 0"
            ))
            logger.info("[022] acc_account.is_group added")

        db.session.commit()
        logger.info("[022] done")
