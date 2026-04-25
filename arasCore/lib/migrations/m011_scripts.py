"""
arasCore/lib/migrations/m011_scripts.py
Create srv_script table for server-side lifecycle hooks.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        if "srv_script" not in set(inspector.get_table_names()):
            db.session.execute(text("""
                CREATE TABLE srv_script (
                    id         INTEGER PRIMARY KEY AUTO_INCREMENT,
                    is_active  BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    name       VARCHAR(100) NOT NULL,
                    app        VARCHAR(80)  NOT NULL,
                    resource   VARCHAR(100) NOT NULL,
                    event      VARCHAR(30)  NOT NULL,
                    code       TEXT NOT NULL DEFAULT '',
                    active     BOOLEAN NOT NULL DEFAULT 1,
                    KEY idx_srv_script (app, resource, event)
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m011] Created srv_script")
        else:
            logger.info("[m011] srv_script already exists, skipping")
