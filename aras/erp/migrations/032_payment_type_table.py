
import logging
logger = logging.getLogger(__name__)

def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.core.extensions import db
    with flask_app.app_context():
        inspector = inspect(db.engine)
        
        # 1. Create erp_payment_type if not exists
        if "erp_payment_type" not in inspector.get_table_names():
            db.session.execute(text("""
                CREATE TABLE erp_payment_type (
                    id         INTEGER PRIMARY KEY AUTO_INCREMENT,
                    is_active  BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    name       VARCHAR(100) NOT NULL UNIQUE,
                    code       VARCHAR(20) NOT NULL UNIQUE,
                    created_by_id INTEGER,
                    updated_by_id INTEGER,
                    FOREIGN KEY(created_by_id) REFERENCES auth_users (id),
                    FOREIGN KEY(updated_by_id) REFERENCES auth_users (id)
                ) CHARACTER SET utf8mb4
            """))
            logger.info("[032] Created erp_payment_type table")

        # 2. Seed default types
        existing_codes = {r[0] for r in db.session.execute(text("SELECT code FROM erp_payment_type")).fetchall()}
        for name, code in [("Cash", "cash"), ("Bank Transfer", "bank"), ("E-Wallet", "ewallet"), ("Other", "other")]:
            if code not in existing_codes:
                db.session.execute(text("INSERT INTO erp_payment_type (name, code) VALUES (:name, :code)"), 
                                 {"name": name, "code": code})
        
        # 3. Add payment_type_id to erp_mode_of_payment if not exists
        if "erp_mode_of_payment" in inspector.get_table_names():
            mop_cols = {c['name'] for c in inspector.get_columns("erp_mode_of_payment")}
            if "payment_type_id" not in mop_cols:
                db.session.execute(text("ALTER TABLE erp_mode_of_payment ADD COLUMN payment_type_id INTEGER NULL"))
                db.session.execute(text("ALTER TABLE erp_mode_of_payment ADD CONSTRAINT fk_mop_payment_type FOREIGN KEY (payment_type_id) REFERENCES erp_payment_type(id)"))
                logger.info("[032] Added payment_type_id to erp_mode_of_payment")

            # 4. Migrate data if 'payment_type' column still exists
            if "payment_type" in mop_cols:
                # Update payment_type_id based on string match in payment_type
                db.session.execute(text("""
                    UPDATE erp_mode_of_payment m
                    JOIN erp_payment_type t ON t.code = m.payment_type
                    SET m.payment_type_id = t.id
                    WHERE m.payment_type_id IS NULL
                """))
                # Drop old column
                db.session.execute(text("ALTER TABLE erp_mode_of_payment DROP COLUMN payment_type"))
                logger.info("[032] Migrated payment_type data and dropped old column")

        db.session.commit()
