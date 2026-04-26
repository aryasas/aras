"""
021 — restructure: drop charge_category, merge payment_type into mode_of_payment,
      add pos_shift_balance, add product.use_price_table
"""
from arasCore.lib.extensions import db


def upgrade():
    conn = db.engine.connect()
    dialect = db.engine.dialect.name

    def col_exists(table, col):
        insp = db.inspect(db.engine)
        return col in [c["name"] for c in insp.get_columns(table)]

    def table_exists(table):
        insp = db.inspect(db.engine)
        return table in insp.get_table_names()

    # 1. Drop category_id FK from charge
    if col_exists("charge", "category_id"):
        if dialect == "mysql":
            conn.execute(db.text(
                "ALTER TABLE charge DROP FOREIGN KEY IF EXISTS charge_ibfk_category"
            ))
        try:
            conn.execute(db.text("ALTER TABLE charge DROP COLUMN category_id"))
        except Exception:
            pass

    # 2. Merge payment_type into mode_of_payment as varchar column
    if table_exists("erp_mode_of_payment") and not col_exists("erp_mode_of_payment", "payment_type"):
        conn.execute(db.text(
            "ALTER TABLE erp_mode_of_payment ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'cash'"
        ))
        # migrate from old payment_type_id FK
        if col_exists("erp_mode_of_payment", "payment_type_id") and table_exists("erp_payment_type"):
            conn.execute(db.text("""
                UPDATE erp_mode_of_payment m
                JOIN erp_payment_type t ON t.id = m.payment_type_id
                SET m.payment_type = t.code
                WHERE m.payment_type_id IS NOT NULL
            """))

    # 3. Drop payment_type_id FK and column from mode_of_payment
    if col_exists("erp_mode_of_payment", "payment_type_id"):
        if dialect == "mysql":
            try:
                conn.execute(db.text(
                    "ALTER TABLE erp_mode_of_payment DROP FOREIGN KEY erp_mode_of_payment_ibfk_1"
                ))
            except Exception:
                pass
        try:
            conn.execute(db.text("ALTER TABLE erp_mode_of_payment DROP COLUMN payment_type_id"))
        except Exception:
            pass

    # 4. Rename company_payment_account unique constraint (company_id → mode_of_payment_id)
    if table_exists("erp_company_payment_account") and col_exists("erp_company_payment_account", "company_id"):
        # Re-key: old PK was (company_id, mode_of_payment_id), new is (mode_of_payment_id, company_id)
        try:
            if dialect == "mysql":
                conn.execute(db.text(
                    "ALTER TABLE erp_company_payment_account DROP INDEX uq_company_mop"
                ))
                conn.execute(db.text(
                    "ALTER TABLE erp_company_payment_account ADD UNIQUE KEY uq_mop_company (mode_of_payment_id, company_id)"
                ))
        except Exception:
            pass

    # 5. Create pos_shift_balance
    if not table_exists("pos_shift_balance"):
        conn.execute(db.text("""
            CREATE TABLE pos_shift_balance (
                id                 BIGINT PRIMARY KEY AUTO_INCREMENT,
                session_id         INT NOT NULL,
                mode_of_payment_id BIGINT NOT NULL,
                opening_balance    DECIMAL(18,4) NOT NULL DEFAULT 0,
                closing_balance    DECIMAL(18,4) NOT NULL DEFAULT 0,
                created_at         DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at         DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_shift_balance_mop (session_id, mode_of_payment_id),
                CONSTRAINT fk_psb_session FOREIGN KEY (session_id) REFERENCES pos_session(id),
                CONSTRAINT fk_psb_mop FOREIGN KEY (mode_of_payment_id) REFERENCES erp_mode_of_payment(id)
            )
        """))

    # 6. Add use_price_table to stock_product
    if table_exists("stock_product") and not col_exists("stock_product", "use_price_table"):
        conn.execute(db.text(
            "ALTER TABLE stock_product ADD COLUMN use_price_table TINYINT(1) NOT NULL DEFAULT 0"
        ))

    conn.close()


def downgrade():
    pass
