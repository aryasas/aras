"""
arasCore/lib/migrations/m005_list_view_setting.py
Create adm_list_view_setting — framework-level per-user list preferences.
Safe to re-run: CREATE TABLE IF NOT EXISTS guard.
"""
import logging

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS `adm_list_view_setting` (
    `id`           INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `created_at`   DATETIME DEFAULT CURRENT_TIMESTAMP,
    `updated_at`   DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `is_active`    TINYINT(1) NOT NULL DEFAULT 1,
    `created_by_id` INT NULL,
    `updated_by_id` INT NULL,
    `user_id`      INT NOT NULL,
    `doctype`      VARCHAR(120) NOT NULL,
    `columns_json` TEXT NULL,
    `page_size`    INT NOT NULL DEFAULT 20,
    `view_mode`    VARCHAR(10) NOT NULL DEFAULT 'list',
    `show_totals`  TINYINT(1) NOT NULL DEFAULT 0,
    UNIQUE KEY `uq_adm_list_view` (`user_id`, `doctype`),
    CONSTRAINT `fk_adm_lv_user` FOREIGN KEY (`user_id`) REFERENCES `auth_users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""


def run(flask_app):
    from arasCore.lib.extensions import db
    from sqlalchemy import text
    with flask_app.app_context():
        with db.engine.begin() as conn:
            conn.execute(text(_DDL))
    logger.info("[m005] adm_list_view_setting: OK")
