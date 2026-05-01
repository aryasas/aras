"""
arasCore/lib/migrations/m016_default_section.py
Add mgr_column.default_section column.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect

        insp = inspect(db.engine)
        cols = {c["name"] for c in insp.get_columns("mgr_column")}
        if "default_section" not in cols:
            db.session.execute(text(
                "ALTER TABLE mgr_column ADD COLUMN default_section VARCHAR(20) NOT NULL DEFAULT 'content'"
            ))
            db.session.commit()
            logger.info("[m016] mgr_column.default_section added")
