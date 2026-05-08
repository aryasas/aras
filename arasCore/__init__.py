# -*- coding: utf-8 -*-
"""arasCore/__init__.py — App factory."""
import os
from flask import Flask
from config import config

from .lib.core.extensions import register_extensions
from .lib.core.database import configure_database
from .lib.core.context import register_context_processors
from .lib.core.utils import set_jinja_env


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

        # Teardown shield — auto_migrate may KILL stale server-side connections
        # that the pool still references. Without this, the next teardown_appcontext
        # tries to ROLLBACK a dead handle and raises "Server has gone away",
        # masking the real result of the request/CLI command.
        from sqlalchemy.exc import InterfaceError as _SAInterfaceError
        from .lib.core.extensions import db as _db_for_teardown

        @app.teardown_appcontext
        def _shield_dead_conn(exc):
            try:
                _db_for_teardown.session.remove()
            except _SAInterfaceError:
                try:
                    _db_for_teardown.engine.dispose(close=True)
                except Exception:
                    pass
            except Exception:
                pass

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

        # Schema migrations are model-driven via auto_migrate (called below).
        # App modules from aras/ gated by DB install status + admin last
        from .lib.services.blueprints import register_app_modules
        register_app_modules(app)

        # Context processors
        register_context_processors(app)

        # Load dynamic apps from DB
        from .admin.services import load_all_built_apps
        load_all_built_apps(app)

        # Auto-migrate: reconcile DB schema to model declarations.
        # Safe ops always; drops gated by ARAS_AUTO_DROP=true.
        try:
            from .lib.services.auto_migrate import run as _auto_migrate
            _auto_migrate(app)
        except Exception as _ame:
            app.logger.error(f"[arasCore] auto_migrate failed: {_ame}", exc_info=True)

        # Universal API — must run after all blueprints registered
        from .lib.services.api_handler import register_universal_api
        register_universal_api(app)

        from .admin.page_actions import register_actions_blueprint
        register_actions_blueprint(app)

        # Webhook dispatcher — subscribe after all events are wired up.
        # Optional: requires `huey`. Silent skip when unavailable.
        try:
            from .lib.services.webhook import init_webhooks
            init_webhooks(app)
        except ImportError:
            pass
        except Exception as _we:
            app.logger.warning(f"[arasCore] webhook init skipped: {_we}")

        # Error handlers
        from .lib.core.error_handler import register_errorhandlers
        register_errorhandlers(app)

        # Health check endpoint + startup validation
        from .lib.core.health import register_health_endpoint, run_startup_checks
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
        from .lib.cli.cli import register_cli
        register_cli(app)

        # Pre-flight schema check (development only)
        try:
            import sys as _sys
            _argv = " ".join(_sys.argv)
            if "migrate" not in _argv and "remigrate" not in _argv:
                from .lib.core.preflight import run_preflight_check
                run_preflight_check(app)
        except Exception as _pe:
            app.logger.debug(f"[preflight] check skipped: {_pe}")

        # Jinja env
        set_jinja_env(app)

        app.logger.info("[arasCore] App started.")

    return app


# Expose db for flask db migrate
from .lib.core.extensions import db  # noqa: E402, F401

# Single-import entrypoint for app code: `from arasCore import ArasGen`
from .arasgen import ArasGen  # noqa: E402, F401

# Lean imports — write `from arasCore import Col, String, Integer, ...` and skip the namespace.
from .arasgen import (  # noqa: E402, F401
    ArasModel, ArasDoc, ArasForm, ArasRoute, ArasDB, ArasApp,
    Col, String, Text, Integer, Decimal, Float, Boolean,
    Date, DateTime, Password, Email, Select, FK,
    auto_resources, auto_menu_groups,
)
