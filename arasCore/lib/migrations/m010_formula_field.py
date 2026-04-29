"""
arasCore/lib/migrations/m010_formula_field.py
Add formula and regex_pattern columns to mgr_column.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        cols = {c["name"] for c in inspector.get_columns("mgr_column")}

        if "formula" not in cols:
            db.session.execute(text("ALTER TABLE mgr_column ADD COLUMN formula TEXT NULL"))
            db.session.commit()
            logger.info("[m010] Added mgr_column.formula")

        if "regex_pattern" not in cols:
            db.session.execute(text("ALTER TABLE mgr_column ADD COLUMN regex_pattern VARCHAR(300) NULL"))
            db.session.commit()
            logger.info("[m010] Added mgr_column.regex_pattern")

        if "formula" in cols and "regex_pattern" in cols:
            logger.info("[m010] formula/regex_pattern already exist, skipping")
