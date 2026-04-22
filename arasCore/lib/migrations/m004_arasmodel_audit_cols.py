# -*- coding: utf-8 -*-
"""
arasCore/lib/migrations/m004_arasmodel_audit_cols.py
=====================================================
Add created_by_id / updated_by_id to every mgr_* and adm_* table that
inherits ArasModel but was created before those columns were added to the
base class.

Safe to re-run: each ALTER checks information_schema first.
"""
import logging

logger = logging.getLogger(__name__)

_TABLES = [
    "mgr_app",
    "mgr_table",
    "mgr_column",
    "mgr_page_action",
    "mgr_page_view",
    "mgr_dashboard",
    "mgr_app_setting",
    "mgr_field",
    "mgr_menu",
    "adm_notification",
    "adm_user_activity",
]

_NEW_COLS = [
    ("created_by_id", "INT NULL"),
    ("updated_by_id", "INT NULL"),
]


def _col_exists(conn, table, column):
    from sqlalchemy import text
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = DATABASE() "
        f"AND TABLE_NAME = '{table}' AND COLUMN_NAME = '{column}'"
    )).scalar()


def _table_exists(conn, table):
    from sqlalchemy import text
    return conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.TABLES "
        "WHERE TABLE_SCHEMA = DATABASE() "
        f"AND TABLE_NAME = '{table}'"
    )).scalar()


def run(flask_app):
    from arasCore.lib.extensions import db
    from sqlalchemy import text

    with flask_app.app_context():
        with db.engine.connect() as conn:
            for tbl in _TABLES:
                if not _table_exists(conn, tbl):
                    logger.info(f"[m004] {tbl} does not exist, skipping")
                    continue
                for col, definition in _NEW_COLS:
                    if _col_exists(conn, tbl, col):
                        continue
                    conn.execute(text(f"ALTER TABLE `{tbl}` ADD COLUMN `{col}` {definition}"))
                    conn.commit()
                    logger.info(f"[m004] ALTER TABLE {tbl} ADD COLUMN {col}")

    logger.info("[m004] audit cols migration complete")
