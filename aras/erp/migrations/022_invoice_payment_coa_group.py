"""
022 — add acc_invoice_payment, acc_account.is_group,
      drop amount_paid/amount_due from invoices,
      drop stock_product: product_type, barcode, cost_price, standard_price
      add stock_product.is_stock_item
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.core.extensions import db
    with flask_app.app_context():
        insp   = inspect(db.engine)
        tables = insp.get_table_names()

        # ── acc_invoice_payment ───────────────────────────────────────────
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

        # ── acc_account.is_group ──────────────────────────────────────────
        acc_cols = {c["name"] for c in insp.get_columns("acc_account")}
        if "is_group" not in acc_cols:
            db.session.execute(text(
                "ALTER TABLE acc_account ADD COLUMN is_group TINYINT(1) NOT NULL DEFAULT 0"
            ))
            logger.info("[022] acc_account.is_group added")

        # ── acc_sales_invoice / acc_purchase_invoice — drop legacy columns ─
        for tbl in ("acc_sales_invoice", "acc_purchase_invoice"):
            if tbl not in tables:
                continue
            cols = {c["name"] for c in insp.get_columns(tbl)}
            for col in ("amount_paid", "amount_due"):
                if col in cols:
                    try:
                        db.session.execute(text(f"ALTER TABLE {tbl} DROP COLUMN {col}"))
                        logger.info(f"[022] {tbl}.{col} dropped")
                    except Exception as e:
                        logger.warning(f"[022] could not drop {tbl}.{col}: {e}")

        # ── stock_product — remove redundant columns, add is_stock_item ──
        if "stock_product" in tables:
            sp_cols = {c["name"] for c in insp.get_columns("stock_product")}
            for col in ("product_type", "barcode", "cost_price", "standard_price"):
                if col in sp_cols:
                    try:
                        db.session.execute(text(f"ALTER TABLE stock_product DROP COLUMN {col}"))
                        logger.info(f"[022] stock_product.{col} dropped")
                    except Exception as e:
                        logger.warning(f"[022] could not drop stock_product.{col}: {e}")
            if "is_stock_item" not in sp_cols:
                db.session.execute(text(
                    "ALTER TABLE stock_product ADD COLUMN is_stock_item TINYINT(1) NOT NULL DEFAULT 1"
                ))
                logger.info("[022] stock_product.is_stock_item added")

        # ── pos_payment.method — change from Enum to VARCHAR ─────────────
        if "pos_payment" in tables:
            try:
                db.session.execute(text(
                    "ALTER TABLE pos_payment MODIFY COLUMN method VARCHAR(100) NOT NULL DEFAULT 'cash'"
                ))
                logger.info("[022] pos_payment.method changed to VARCHAR")
            except Exception as e:
                logger.warning(f"[022] pos_payment.method: {e}")

        db.session.commit()
        logger.info("[022] done")
