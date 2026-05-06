"""
Migration 033 — Split pos_terminal.pricelist_id into selling_pricelist_id + purchase_pricelist_id
"""
from arasCore.lib.core.extensions import db


def run(flask_app):
    with flask_app.app_context():
        up()


def up():
    conn  = db.engine.connect()
    trans = conn.begin()
    try:
        # Check if old column still exists
        has_old = conn.execute(db.text(
            "SELECT COUNT(*) FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pos_terminal' "
            "AND COLUMN_NAME = 'pricelist_id'"
        )).scalar()

        conn.execute(db.text("ALTER TABLE pos_terminal ADD COLUMN IF NOT EXISTS selling_pricelist_id INT NULL"))
        conn.execute(db.text("ALTER TABLE pos_terminal ADD COLUMN IF NOT EXISTS purchase_pricelist_id INT NULL"))

        if has_old:
            conn.execute(db.text("UPDATE pos_terminal SET selling_pricelist_id = pricelist_id"))
            fk_row = conn.execute(db.text(
                "SELECT CONSTRAINT_NAME FROM information_schema.KEY_COLUMN_USAGE "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pos_terminal' "
                "AND COLUMN_NAME = 'pricelist_id' AND REFERENCED_TABLE_NAME IS NOT NULL LIMIT 1"
            )).fetchone()
            if fk_row:
                conn.execute(db.text(f"ALTER TABLE pos_terminal DROP FOREIGN KEY `{fk_row[0]}`"))
            conn.execute(db.text("ALTER TABLE pos_terminal DROP COLUMN pricelist_id"))

        # Add FK constraints (ignore if already exist)
        for name, col in [("fk_pt_selling_pl", "selling_pricelist_id"), ("fk_pt_purchase_pl", "purchase_pricelist_id")]:
            exists = conn.execute(db.text(
                "SELECT COUNT(*) FROM information_schema.TABLE_CONSTRAINTS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'pos_terminal' "
                f"AND CONSTRAINT_NAME = '{name}'"
            )).scalar()
            if not exists:
                conn.execute(db.text(
                    f"ALTER TABLE pos_terminal ADD CONSTRAINT {name} "
                    f"FOREIGN KEY ({col}) REFERENCES stock_price_list(id) ON DELETE SET NULL"
                ))

        trans.commit()
    except Exception:
        trans.rollback()
        raise
    finally:
        conn.close()
