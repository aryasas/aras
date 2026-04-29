"""
arasCore/lib/migrations/m008_audit_field_log.py
Create audit_field_log table for field-level change versioning.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        if "audit_field_log" not in set(inspector.get_table_names()):
            db.session.execute(text("""
                CREATE TABLE audit_field_log (
                    id            BIGINT PRIMARY KEY AUTO_INCREMENT,
                    is_active     BOOLEAN NOT NULL DEFAULT 1,
                    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    app           VARCHAR(80)  NOT NULL,
                    resource      VARCHAR(100) NOT NULL,
                    object_id     INTEGER NULL,
                    field_name    VARCHAR(100) NOT NULL,
                    old_value     TEXT NULL,
                    new_value     TEXT NULL,
                    changed_by_id INTEGER NULL,
                    changed_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_audit_field (resource, object_id)
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m008] Created audit_field_log")
        else:
            logger.info("[m008] audit_field_log already exists, skipping")
