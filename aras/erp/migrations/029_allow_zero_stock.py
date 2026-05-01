"""Migration 029 — Add allow_zero_stock to company, stock_product_category, stock_product."""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(db.text(
            "ALTER TABLE company ADD COLUMN IF NOT EXISTS allow_zero_stock TINYINT(1) NOT NULL DEFAULT 0"
        ))
        conn.execute(db.text(
            "ALTER TABLE stock_product_category ADD COLUMN IF NOT EXISTS allow_zero_stock TINYINT(1) NULL DEFAULT NULL"
        ))
        conn.execute(db.text(
            "ALTER TABLE stock_product ADD COLUMN IF NOT EXISTS allow_zero_stock TINYINT(1) NULL DEFAULT NULL"
        ))
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
