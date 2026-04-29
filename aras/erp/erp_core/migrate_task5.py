"""
Sprint B+C DB migration — idempotent:
- pos_order_line: add uom_id, qty_base
- pos_terminal: add warehouse_id, pricelist_id
"""
from arasCore.lib.core.extensions import db


def _col_exists(table, col):
    row = db.session.execute(db.text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_schema=DATABASE() AND table_name=:t AND column_name=:c"
    ), {"t": table, "c": col}).scalar()
    return row > 0


def _add_col(table, col, definition):
    if not _col_exists(table, col):
        db.session.execute(db.text(f"ALTER TABLE `{table}` ADD COLUMN `{col}` {definition}"))
        db.session.commit()


def _seq_exists(company_id, code):
    row = db.session.execute(db.text(
        "SELECT COUNT(*) FROM core_sequence WHERE company_id=:c AND code=:code"
    ), {"c": company_id, "code": code}).scalar()
    return row > 0


def _get_hq_company_id():
    row = db.session.execute(db.text(
        "SELECT id FROM core_company ORDER BY id LIMIT 1"
    )).fetchone()
    return row[0] if row else None


def run(app):
    with app.app_context():
        _add_col("pos_order_line", "uom_id",      "INT NULL")
        _add_col("pos_order_line", "qty_base",     "DECIMAL(12,6) NOT NULL DEFAULT 0")
        _add_col("pos_terminal",   "warehouse_id", "INT NULL")
        _add_col("pos_terminal",   "pricelist_id", "INT NULL")

        # Insert stock.move sequence if missing
        cid = _get_hq_company_id()
        if cid and not _seq_exists(cid, "stock.move"):
            db.session.execute(db.text(
                "INSERT INTO core_sequence (company_id, code, prefix, padding, reset_period, next_value) "
                "VALUES (:cid, 'stock.move', 'SM', 5, 'yearly', 0)"
            ), {"cid": cid})
            db.session.commit()
