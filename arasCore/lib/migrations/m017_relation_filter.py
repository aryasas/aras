"""
arasCore/lib/migrations/m017_relation_filter.py
Add mgr_column.relation_filter — SQL WHERE snippet for combobox filtering.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect

        insp = inspect(db.engine)
        cols = {c["name"] for c in insp.get_columns("mgr_column")}
        if "relation_filter" not in cols:
            db.session.execute(text(
                "ALTER TABLE mgr_column ADD COLUMN relation_filter VARCHAR(500) NULL"
            ))
            db.session.commit()
            logger.info("[m017] mgr_column.relation_filter added")
