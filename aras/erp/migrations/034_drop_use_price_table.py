"""Migration 034 — Drop use_price_table column from stock_product."""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(db.text(
            "ALTER TABLE stock_product DROP COLUMN IF EXISTS use_price_table"
        ))
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
