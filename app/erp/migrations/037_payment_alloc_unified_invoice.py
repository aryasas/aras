"""037 — Unify payment allocation: replace sales_invoice_id/purchase_invoice_id with invoice_type/invoice_id."""
from arasCore.lib.core.extensions import db


def upgrade():
    with db.engine.connect() as conn:
        conn.execute(db.text("""
            ALTER TABLE acc_payment_allocation
                ADD COLUMN invoice_type VARCHAR(10) NULL,
                ADD COLUMN invoice_id   BIGINT NULL
        """))
        # Migrate existing data
        conn.execute(db.text("""
            UPDATE acc_payment_allocation
               SET invoice_type = 'sales', invoice_id = sales_invoice_id
             WHERE sales_invoice_id IS NOT NULL
        """))
        conn.execute(db.text("""
            UPDATE acc_payment_allocation
               SET invoice_type = 'purchase', invoice_id = purchase_invoice_id
             WHERE purchase_invoice_id IS NOT NULL AND invoice_id IS NULL
        """))
        conn.commit()
        # Drop old columns
        conn.execute(db.text("ALTER TABLE acc_payment_allocation DROP FOREIGN KEY IF EXISTS acc_payment_allocation_ibfk_2"))
        conn.execute(db.text("ALTER TABLE acc_payment_allocation DROP FOREIGN KEY IF EXISTS acc_payment_allocation_ibfk_3"))
        try:
            conn.execute(db.text("ALTER TABLE acc_payment_allocation DROP COLUMN sales_invoice_id"))
        except Exception:
            pass
        try:
            conn.execute(db.text("ALTER TABLE acc_payment_allocation DROP COLUMN purchase_invoice_id"))
        except Exception:
            pass
        conn.commit()


def downgrade():
    pass
