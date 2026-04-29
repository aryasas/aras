# -*- coding: utf-8 -*-
"""
arasCore/lib/migrations/m003_dynamic_app_migrations.py
=======================================================
Create the per-dynamic-app migration tracking table used by the schema
migration runner (arasCore/lib/schema_migrator.py).

Safe to re-run: uses CREATE TABLE IF NOT EXISTS.
"""
import logging

logger = logging.getLogger(__name__)


def run(_flask_app):
    from arasCore.lib.core.extensions import db
    from sqlalchemy import text

    with db.engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS `mgr_schema_migration` (
                `id`          INT AUTO_INCREMENT PRIMARY KEY,
                `app_name`    VARCHAR(100) NOT NULL,
                `table_name`  VARCHAR(200) NOT NULL,
                `column_name` VARCHAR(200) NOT NULL,
                `action`      VARCHAR(20)  NOT NULL DEFAULT 'add_column',
                `status`      VARCHAR(20)  NOT NULL DEFAULT 'pending',
                `sql_stmt`    TEXT         NULL,
                `error_msg`   TEXT         NULL,
                `created_at`  DATETIME     DEFAULT CURRENT_TIMESTAMP,
                `applied_at`  DATETIME     NULL,
                INDEX `idx_app_table` (`app_name`, `table_name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """))
        conn.commit()

    logger.info("[m003] mgr_schema_migration table ready")
