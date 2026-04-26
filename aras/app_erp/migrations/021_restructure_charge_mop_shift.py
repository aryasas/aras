"""
021 — drop charge_category, merge payment_type into mode_of_payment,
      add pos_shift_balance, add product.use_price_table
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.extensions import db
    with flask_app.app_context():
        insp   = inspect(db.engine)
        tables = insp.get_table_names()

        # Drop charge_category FK from charge table
        charge_cols = {c["name"] for c in insp.get_columns("charge")} if "charge" in tables else set()
        if "category_id" in charge_cols:
            db.session.execute(text("ALTER TABLE charge DROP COLUMN category_id"))
            logger.info("[021] charge.category_id dropped")

        # Merge payment_type into mode_of_payment
        if "erp_mode_of_payment" in tables:
            mop_cols = {c["name"] for c in insp.get_columns("erp_mode_of_payment")}
            if "payment_type" not in mop_cols and "type" in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment CHANGE type payment_type VARCHAR(20) NOT NULL DEFAULT 'cash'"))
                logger.info("[021] erp_mode_of_payment.type renamed to payment_type")
            elif "payment_type" not in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment ADD COLUMN payment_type VARCHAR(20) NOT NULL DEFAULT 'cash'"))
                logger.info("[021] erp_mode_of_payment.payment_type added")
            if "payment_type_id" in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment DROP COLUMN payment_type_id"))
                logger.info("[021] erp_mode_of_payment.payment_type_id dropped")

        # pos_shift_balance
        if "pos_shift_balance" not in tables:
            db.session.execute(text("""
                CREATE TABLE pos_shift_balance (
                    id                  INTEGER AUTO_INCREMENT PRIMARY KEY,
                    session_id          INTEGER NOT NULL,
                    mode_of_payment_id  INTEGER NOT NULL,
                    opening_balance     NUMERIC(18,4) NOT NULL DEFAULT 0,
                    closing_balance     NUMERIC(18,4) NOT NULL DEFAULT 0,
                    is_active           TINYINT(1) NOT NULL DEFAULT 1,
                    created_at          DATETIME DEFAULT NOW(),
                    updated_at          DATETIME DEFAULT NOW(),
                    created_by_id       INTEGER,
                    updated_by_id       INTEGER,
                    UNIQUE KEY uq_shift_balance_mop (session_id, mode_of_payment_id)
                )
            """))
            logger.info("[021] pos_shift_balance created")

        # product.use_price_table
        if "stock_product" in tables:
            prod_cols = {c["name"] for c in insp.get_columns("stock_product")}
            if "use_price_table" not in prod_cols:
                db.session.execute(text("ALTER TABLE stock_product ADD COLUMN use_price_table TINYINT(1) NOT NULL DEFAULT 0"))
                logger.info("[021] stock_product.use_price_table added")

        db.session.commit()
        logger.info("[021] done")
