"""Migration: create erp_list_view_setting, erp_report, erp_report_favorite; alter pos_session add shift_number"""
from arasCore.lib.extensions import db


def up(app):
    with app.app_context():
        conn = db.engine.connect()

        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS erp_list_view_setting (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                user_id      INT NOT NULL,
                doctype      VARCHAR(100) NOT NULL,
                columns_json TEXT,
                filters_json TEXT,
                page_size    INT NOT NULL DEFAULT 20,
                updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY uq_list_view_user_doctype (user_id, doctype),
                CONSTRAINT fk_lvs_user FOREIGN KEY (user_id) REFERENCES auth_users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS erp_report (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                company_id   INT NULL,
                name         VARCHAR(100) NOT NULL UNIQUE,
                title        VARCHAR(200) NOT NULL,
                module       VARCHAR(50) NOT NULL DEFAULT 'general',
                report_type  ENUM('query','script','jinja') NOT NULL DEFAULT 'query',
                script       TEXT,
                columns_json TEXT,
                filters_json TEXT,
                is_active    TINYINT(1) NOT NULL DEFAULT 1,
                created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                created_by   INT NULL,
                CONSTRAINT fk_rpt_company  FOREIGN KEY (company_id)  REFERENCES core_company(id),
                CONSTRAINT fk_rpt_creator  FOREIGN KEY (created_by)  REFERENCES auth_users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        conn.execute(db.text("""
            CREATE TABLE IF NOT EXISTS erp_report_favorite (
                id        INT AUTO_INCREMENT PRIMARY KEY,
                user_id   INT NOT NULL,
                report_id INT NOT NULL,
                UNIQUE KEY uq_report_favorite (user_id, report_id),
                CONSTRAINT fk_rf_user   FOREIGN KEY (user_id)   REFERENCES auth_users(id),
                CONSTRAINT fk_rf_report FOREIGN KEY (report_id) REFERENCES erp_report(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))

        # add shift_number to pos_session if not exists
        rows = conn.execute(db.text("""
            SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME='pos_session' AND COLUMN_NAME='shift_number'
            AND TABLE_SCHEMA=DATABASE()
        """)).scalar()
        if not rows:
            conn.execute(db.text("""
                ALTER TABLE pos_session ADD COLUMN shift_number VARCHAR(30) NULL
            """))

        conn.commit()
        conn.close()
        print("[migration] 001_erp_features done.")
