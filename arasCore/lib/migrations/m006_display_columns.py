"""
arasCore/lib/migrations/m006_display_columns.py
Add display_columns to mgr_table — controls which fields are shown when this
table is referenced as a FK target (e.g. "code,name" → "1100 — Cash").
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        cols = {c["name"] for c in inspector.get_columns("mgr_table")}
        if "display_columns" not in cols:
            db.session.execute(text(
                "ALTER TABLE mgr_table ADD COLUMN display_columns VARCHAR(200) NULL"
            ))
            db.session.commit()
            logger.info("[m006] Added mgr_table.display_columns")
        else:
            logger.info("[m006] display_columns already exists, skipping")
