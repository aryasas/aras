"""023 — create sup_supplier table"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    from sqlalchemy import text, inspect
    from arasCore.lib.core.extensions import db
    with flask_app.app_context():
        tables = inspect(db.engine).get_table_names()
        if "sup_supplier" not in tables:
            db.session.execute(text("""
                CREATE TABLE sup_supplier (
                    id                INT AUTO_INCREMENT PRIMARY KEY,
                    company_id        INT NOT NULL,
                    code              VARCHAR(30) NOT NULL,
                    name              VARCHAR(200) NOT NULL,
                    type              ENUM('individual','company') NOT NULL DEFAULT 'company',
                    email             VARCHAR(120),
                    phone             VARCHAR(50),
                    mobile            VARCHAR(50),
                    address           TEXT,
                    city              VARCHAR(100),
                    country           VARCHAR(100),
                    tax_id            VARCHAR(50),
                    currency_id       INT,
                    payment_term_days INT DEFAULT 30,
                    credit_limit      DECIMAL(18,4) DEFAULT 0,
                    bank_name         VARCHAR(100),
                    bank_account_no   VARCHAR(50),
                    bank_account_name VARCHAR(200),
                    notes             TEXT,
                    is_active         TINYINT(1) NOT NULL DEFAULT 1,
                    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    deleted_at        DATETIME,
                    created_by_id     INT,
                    updated_by_id     INT,
                    UNIQUE KEY uq_sup_supplier_code (company_id, code),
                    KEY idx_sup_supplier_name (company_id, name),
                    CONSTRAINT fk_sup_supplier_company  FOREIGN KEY (company_id)  REFERENCES company(id),
                    CONSTRAINT fk_sup_supplier_currency FOREIGN KEY (currency_id) REFERENCES currency(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """))
            db.session.commit()
            logger.info("[023] sup_supplier table created")
        else:
            logger.info("[023] sup_supplier already exists, skipping")
