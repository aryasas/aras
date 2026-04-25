"""
arasCore/lib/migrations/m009_webhook.py
Create wh_endpoint table for outbound webhook registration.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        if "wh_endpoint" not in set(inspector.get_table_names()):
            db.session.execute(text("""
                CREATE TABLE wh_endpoint (
                    id         INTEGER PRIMARY KEY AUTO_INCREMENT,
                    is_active  BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    name       VARCHAR(100) NOT NULL,
                    url        VARCHAR(500) NOT NULL,
                    event      VARCHAR(200) NOT NULL,
                    secret     VARCHAR(200) NULL,
                    active     BOOLEAN NOT NULL DEFAULT 1
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m009] Created wh_endpoint")
        else:
            logger.info("[m009] wh_endpoint already exists, skipping")
