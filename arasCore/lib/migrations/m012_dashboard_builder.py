"""
arasCore/lib/migrations/m012_dashboard_builder.py
Add user_id, role_id, layout_json to mgr_dashboard for the dashboard builder.
"""
import logging
logger = logging.getLogger(__name__)


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)
        cols = {c["name"] for c in inspector.get_columns("mgr_dashboard")}

        added = []
        if "user_id" not in cols:
            db.session.execute(text("ALTER TABLE mgr_dashboard ADD COLUMN user_id INTEGER NULL"))
            added.append("user_id")
        if "role_id" not in cols:
            db.session.execute(text("ALTER TABLE mgr_dashboard ADD COLUMN role_id INTEGER NULL"))
            added.append("role_id")
        if "layout_json" not in cols:
            db.session.execute(text("ALTER TABLE mgr_dashboard ADD COLUMN layout_json TEXT NULL"))
            added.append("layout_json")

        if added:
            db.session.commit()
            logger.info(f"[m012] Added mgr_dashboard columns: {added}")
        else:
            logger.info("[m012] mgr_dashboard columns already exist, skipping")
