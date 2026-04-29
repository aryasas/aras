"""
arasCore/lib/migrations/m014_child_tab_footer.py
Add mgr_column.view_in_tab and mgr_table.footer_totals_fields columns.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect

        insp = inspect(db.engine)

        mgr_col_cols = {c["name"] for c in insp.get_columns("mgr_column")}
        if "view_in_tab" not in mgr_col_cols:
            db.session.execute(text(
                "ALTER TABLE mgr_column ADD COLUMN view_in_tab BOOLEAN NOT NULL DEFAULT FALSE"
            ))
            logger.info("[m014] mgr_column.view_in_tab added")

        mgr_tbl_cols = {c["name"] for c in insp.get_columns("mgr_table")}
        if "footer_totals_fields" not in mgr_tbl_cols:
            db.session.execute(text(
                "ALTER TABLE mgr_table ADD COLUMN footer_totals_fields VARCHAR(500)"
            ))
            logger.info("[m014] mgr_table.footer_totals_fields added")

        db.session.commit()
