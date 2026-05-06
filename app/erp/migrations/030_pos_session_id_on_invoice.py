"""
Migration 030 — Replace pos_order_id with pos_session_id on sales/purchase invoices.
Drop pos_order, pos_order_line, pos_payment tables.
"""


def run(flask_app):
    from arasCore.lib.core.extensions import db
    with flask_app.app_context():
        conn  = db.engine.connect()
        trans = conn.begin()
        try:
            upgrade(conn)
            trans.commit()
        except Exception:
            trans.rollback()
            raise
        finally:
            conn.close()


def upgrade(conn):
    def col_exists(table, col):
        r = conn.execute(f"SHOW COLUMNS FROM `{table}` LIKE '{col}'").fetchone()
        return r is not None

    def fk_exists(table, fk_name):
        r = conn.execute(
            "SELECT 1 FROM information_schema.TABLE_CONSTRAINTS "
            f"WHERE TABLE_NAME='{table}' AND CONSTRAINT_NAME='{fk_name}' "
            "AND TABLE_SCHEMA=DATABASE()"
        ).fetchone()
        return r is not None

    # ── acc_sales_invoice ────────────────────────────────────────────────────
    if col_exists("acc_sales_invoice", "pos_order_id"):
        if fk_exists("acc_sales_invoice", "acc_sales_invoice_ibfk_pos_order"):
            conn.execute("ALTER TABLE acc_sales_invoice DROP FOREIGN KEY acc_sales_invoice_ibfk_pos_order")
        conn.execute("ALTER TABLE acc_sales_invoice DROP COLUMN pos_order_id")

    if not col_exists("acc_sales_invoice", "pos_session_id"):
        conn.execute(
            "ALTER TABLE acc_sales_invoice "
            "ADD COLUMN pos_session_id INT NULL, "
            "ADD INDEX ix_sal_inv_pos_session (pos_session_id)"
        )

    # ── acc_purchase_invoice ─────────────────────────────────────────────────
    if col_exists("acc_purchase_invoice", "pos_order_id"):
        if fk_exists("acc_purchase_invoice", "acc_purchase_invoice_ibfk_pos_order"):
            conn.execute("ALTER TABLE acc_purchase_invoice DROP FOREIGN KEY acc_purchase_invoice_ibfk_pos_order")
        conn.execute("ALTER TABLE acc_purchase_invoice DROP COLUMN pos_order_id")

    if not col_exists("acc_purchase_invoice", "pos_session_id"):
        conn.execute(
            "ALTER TABLE acc_purchase_invoice "
            "ADD COLUMN pos_session_id INT NULL, "
            "ADD INDEX ix_pur_inv_pos_session (pos_session_id)"
        )

    # ── drop pos_order tables ────────────────────────────────────────────────
    for table in ("pos_payment", "pos_order_line", "pos_order"):
        try:
            conn.execute(f"DROP TABLE IF EXISTS `{table}`")
        except Exception:
            pass
