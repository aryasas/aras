"""
arasCore/lib/migrations/m013_system_settings.py
Create aras_system_setting table and seed framework-level toggles.
"""
import logging
logger = logging.getLogger(__name__)

_SEEDS = [
    {
        "key": "script_sandbox_extended",
        "label": "Server Script: Allow Extended Modules",
        "value": "false",
        "value_type": "boolean",
        "help_text": "When ON, scripts may use: datetime, math, re, json, decimal. When OFF, only safe builtins.",
        "section": "scripting",
    },
    {
        "key": "dashboard_builder_enabled",
        "label": "Dashboard Builder: Allow User Customization",
        "value": "false",
        "value_type": "boolean",
        "help_text": "When ON, users can build and save their own dashboard widgets from the UI.",
        "section": "dashboard",
    },
]


def run(flask_app):
    with flask_app.app_context():
        from arasCore.lib.core.extensions import db
        from sqlalchemy import text, inspect as sa_inspect
        inspector = sa_inspect(db.engine)

        if "aras_system_setting" not in set(inspector.get_table_names()):
            db.session.execute(text("""
                CREATE TABLE aras_system_setting (
                    id         INTEGER PRIMARY KEY AUTO_INCREMENT,
                    is_active  BOOLEAN NOT NULL DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    key        VARCHAR(100) NOT NULL,
                    label      VARCHAR(200) NULL,
                    value      TEXT NULL,
                    value_type VARCHAR(20) NOT NULL DEFAULT 'string',
                    help_text  VARCHAR(500) NULL,
                    section    VARCHAR(100) NULL DEFAULT 'general',
                    UNIQUE KEY uq_aras_system_setting_key (key)
                ) CHARACTER SET utf8mb4
            """))
            db.session.commit()
            logger.info("[m013] Created aras_system_setting")

        # Seed defaults (skip if key already exists)
        existing = {
            r[0] for r in db.session.execute(
                text("SELECT `key` FROM aras_system_setting")
            ).fetchall()
        }
        for seed in _SEEDS:
            if seed["key"] not in existing:
                db.session.execute(text(
                    "INSERT INTO aras_system_setting (key, label, value, value_type, help_text, section) "
                    "VALUES (:key, :label, :value, :value_type, :help_text, :section)"
                ), seed)
        db.session.commit()
        logger.info("[m013] aras_system_setting seeded")
