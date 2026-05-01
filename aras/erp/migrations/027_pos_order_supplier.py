"""
Migration 027 — Add supplier_id to pos_order
"""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        conn.execute(db.text(
            "ALTER TABLE pos_order ADD COLUMN IF NOT EXISTS supplier_id INTEGER REFERENCES sup_supplier(id)"
        ))
        conn.execute(db.text(
            "CREATE INDEX IF NOT EXISTS idx_pos_order_supplier ON pos_order (supplier_id)"
        ))
        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
