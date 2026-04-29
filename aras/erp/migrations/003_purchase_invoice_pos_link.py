"""003_purchase_invoice_pos_link — add pos_order_id to acc_purchase_invoice."""
from arasCore.lib.core.extensions import db


def upgrade():
    conn = db.engine.connect()
    try:
        conn.execute(db.text(
            "ALTER TABLE acc_purchase_invoice "
            "ADD COLUMN IF NOT EXISTS pos_order_id BIGINT REFERENCES pos_order(id)"
        ))
        conn.commit()
    finally:
        conn.close()
