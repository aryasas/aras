"""
arasCore/lib/migrations/m007_workflow.py
Create wf_state and wf_history tables for the workflow engine.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        existing = set(inspector.get_table_names())

        if "wf_state" not in existing:
            db.session.execute(text("""
                CREATE TABLE wf_state (
                    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
                    is_active       BOOLEAN NOT NULL DEFAULT 1,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    definition_name VARCHAR(100) NOT NULL,
                    object_id       INTEGER NOT NULL,
                    current_state   VARCHAR(100) NOT NULL,
                    updated_by_id   INTEGER NULL,
                    updated_at      DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_wf_state (definition_name, object_id),
                    KEY idx_wf_state (definition_name, object_id)
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m007] Created wf_state")

        if "wf_history" not in existing:
            db.session.execute(text("""
                CREATE TABLE wf_history (
                    id              BIGINT PRIMARY KEY AUTO_INCREMENT,
                    is_active       BOOLEAN NOT NULL DEFAULT 1,
                    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
                    definition_name VARCHAR(100) NOT NULL,
                    object_id       INTEGER NOT NULL,
                    from_state      VARCHAR(100) NOT NULL,
                    to_state        VARCHAR(100) NOT NULL,
                    action          VARCHAR(100) NOT NULL,
                    user_id         INTEGER NULL,
                    note            VARCHAR(500) DEFAULT '',
                    KEY idx_wf_history (definition_name, object_id)
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m007] Created wf_history")
        else:
            logger.info("[m007] wf tables already exist, skipping")
