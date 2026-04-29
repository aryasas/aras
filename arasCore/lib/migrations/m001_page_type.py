# -*- coding: utf-8 -*-
"""
arasCore/lib/migrations/m001_page_type.py
=========================================
Idempotent migration to bring `mgr_table` up to the DocType-style contract and
create companion tables (mgr_page_action, mgr_page_view, mgr_dashboard,
mgr_app_setting).

Safe to re-run: each ALTER checks information_schema first.
"""
import logging

logger = logging.getLogger(__name__)


# (column_name, DDL fragment after `ADD COLUMN`)
MGR_TABLE_NEW_COLUMNS = [
    ("page_type",        "VARCHAR(20) DEFAULT 'list'"),
    ("description",      "VARCHAR(500) NULL"),
    ("icon",             "VARCHAR(50) NULL"),
    ("show_in_home",     "TINYINT(1) DEFAULT 1"),
    ("is_submittable",   "TINYINT(1) DEFAULT 0"),
    ("track_changes",    "TINYINT(1) DEFAULT 0"),
    ("naming_rule",      "VARCHAR(20) DEFAULT 'auto'"),
    ("autoname_pattern", "VARCHAR(100) NULL"),
    ("layout_json",      "TEXT NULL"),
]


def run(flask_app):
    """Apply migration. Idempotent."""
    from arasCore.lib.core.extensions import db
    from sqlalchemy import text

    with flask_app.app_context():
        engine = db.engine
        with engine.begin() as conn:
            # 1. Add new columns to mgr_table
            for col, ddl in MGR_TABLE_NEW_COLUMNS:
                exists = conn.execute(text(
                    "SELECT COUNT(*) FROM information_schema.COLUMNS "
                    "WHERE TABLE_SCHEMA = DATABASE() "
                    "AND TABLE_NAME = 'mgr_table' "
                    f"AND COLUMN_NAME = '{col}'"
                )).scalar()
                if not exists:
                    conn.execute(text(f"ALTER TABLE mgr_table ADD COLUMN {col} {ddl}"))
                    logger.info(f"[m001] mgr_table.{col} added")

            # 2. Create companion tables via SQLAlchemy metadata (idempotent checkfirst=True)
            from arasCore.admin.models import (
                AppManagerPageAction, AppManagerPageView,
                AppManagerDashboard, AppManagerSetting,
            )
            for model in (AppManagerPageAction, AppManagerPageView,
                          AppManagerDashboard, AppManagerSetting):
                model.__table__.create(engine, checkfirst=True)
                logger.info(f"[m001] ensured table {model.__tablename__}")

        logger.info("[m001] migration complete.")
