# -*- coding: utf-8 -*-
"""arasCore/__init__.py — App factory."""
import os
from flask import Flask
from config import config

from .lib.extensions import register_extensions
from .lib.database import configure_database
from .lib.context import register_context_processors
from .lib.utils import set_jinja_env


def _read_mode_file():
    """Read instance/mode.json — returns 'development' or 'production'."""
    import json
    project_root = os.path.dirname(os.path.abspath(__file__))
    mode_file = os.path.join(os.path.dirname(project_root), "instance", "mode.json")
    try:
        with open(mode_file, "r") as f:
            return json.load(f).get("mode", "default")
    except Exception:
        return None


def create_app(config_type=None):
    if config_type is None:
        env_key  = os.getenv("ARAS_CONFIG")
        file_key = _read_mode_file()
        key      = env_key or file_key or "default"
        config_type = config.get(key, config["default"])

    # Project root is one level up from arasCore/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(project_root, "templates"),
                static_folder=os.path.join(project_root, "static"))

    with app.app_context():
        app.config.from_object(config_type)
        app.secret_key = app.config["SECRET_KEY"]

        from datetime import datetime as _dt
        app.config["_SERVER_START_TIME"] = _dt.utcnow()

        # Extensions must be first
        register_extensions(app)

        # Import models in correct order — permissions before auth
        # so SQLAlchemy mapper resolves UserRole ↔ User correctly
        from . import permissions   # noqa: F401
        from . import auth          # noqa: F401
        from .routes import auth_bp
        app.register_blueprint(auth_bp)

        # Root redirect
        from flask import redirect, url_for
        from flask_login import current_user

        @app.route("/")
        def root():
            if current_user.is_authenticated:
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("auth.login_view"))

        # Database — create tables first so _is_app_enabled() can query AppManagerApp
        configure_database(app)

        # arasCore idempotent migrations (must run BEFORE querying mgr_* tables)
        try:
            from .lib.migrations import m001_page_type
            m001_page_type.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m001 skipped: {_me}")

        try:
            from .lib.migrations import m002_rbac
            m002_rbac.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m002 skipped: {_me}")

        try:
            from .lib.migrations import m004_arasmodel_audit_cols
            m004_arasmodel_audit_cols.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m004 skipped: {_me}")

        try:
            from .lib.migrations import m005_list_view_setting
            m005_list_view_setting.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m005 skipped: {_me}")

        try:
            from .lib.migrations import m006_display_columns
            m006_display_columns.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m006 skipped: {_me}")

        try:
            from .lib.migrations import m007_workflow
            m007_workflow.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m007 skipped: {_me}")

        try:
            from .lib.migrations import m008_audit_field_log
            m008_audit_field_log.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m008 skipped: {_me}")

        try:
            from .lib.migrations import m009_webhook
            m009_webhook.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m009 skipped: {_me}")

        try:
            from .lib.migrations import m010_formula_field
            m010_formula_field.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m010 skipped: {_me}")

        try:
            from .lib.migrations import m011_scripts
            m011_scripts.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m011 skipped: {_me}")

        try:
            from .lib.migrations import m012_dashboard_builder
            m012_dashboard_builder.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m012 skipped: {_me}")

        try:
            from .lib.migrations import m013_system_settings
            m013_system_settings.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m013 skipped: {_me}")

        try:
            from .lib.migrations import m014_child_tab_footer
            m014_child_tab_footer.run(app)
        except Exception as _me:
            app.logger.warning(f"[arasCore] migration m014 skipped: {_me}")

        # App modules from aras/ gated by DB install status + arasAdmin last
        from .lib.blueprints import register_app_modules
        register_app_modules(app)

        # Context processors
        register_context_processors(app)

        # Load dynamic apps from DB
        from .arasAdmin.services import load_all_built_apps
        load_all_built_apps(app)

        # Universal API — must run after all blueprints registered
        from .lib.api_handler import register_universal_api
        register_universal_api(app)

        from .arasAdmin.page_actions import register_actions_blueprint
        register_actions_blueprint(app)

        # Webhook dispatcher — subscribe after all events are wired up
        try:
            from .lib.webhook import init_webhooks
            init_webhooks(app)
        except Exception as _we:
            app.logger.warning(f"[arasCore] webhook init skipped: {_we}")

        # Error handlers
        from .lib.error_handler import register_errorhandlers
        register_errorhandlers(app)

        # Health check endpoint + startup validation
        from .lib.health import register_health_endpoint, run_startup_checks
        register_health_endpoint(app)
        try:
            result = run_startup_checks(app)
            if result["errors"]:
                app.logger.warning(f"[health] {len(result['errors'])} resource(s) failed build: "
                                   f"{[e['resource'] for e in result['errors']]}")
            else:
                app.logger.info(f"[health] {len(result['ok'])} resource(s) OK.")
        except Exception as _he:
            app.logger.warning(f"[health] startup check skipped: {_he}")

        # CLI commands (aras install-app, list-apps, etc.)
        from .lib.cli import register_cli
        register_cli(app)

        # Jinja env
        set_jinja_env(app)

        app.logger.info("[arasCore] App started.")

    return app


# Expose db for flask db migrate
from .lib.extensions import db  # noqa: E402, F401
