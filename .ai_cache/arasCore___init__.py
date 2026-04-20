# -*- coding: utf-8 -*-
"""arasCore/__init__.py — App factory."""
import os
from flask import Flask
from config import config

from .lib.extensions import register_extensions
from .lib.database import configure_database
from .lib.context import register_context_processors
from .lib.utils import set_jinja_env


def create_app(config_type=None):
    if config_type is None:
        config_type = config.get(
            os.getenv("ARAS_CONFIG", "default"), config["default"]
        )

    # Project root is one level up from arasCore/
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__,
                template_folder=os.path.join(project_root, "templates"),
                static_folder=os.path.join(project_root, "static"))

    with app.app_context():
        app.config.from_object(config_type)
        app.secret_key = app.config["SECRET_KEY"]

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

        # App modules from aras/ (app_basic, etc.) + arasAdmin last
        from .lib.blueprints import register_app_modules
        register_app_modules(app)

        # Database — create tables
        configure_database(app)

        # Context processors
        register_context_processors(app)

        # Load dynamic apps from DB
        from .arasAdmin.services import load_all_built_apps
        load_all_built_apps(app)

        # Universal API — must run after all blueprints registered
        from .lib.api_handler import register_universal_api
        register_universal_api(app)

        # Error handlers
        from .lib.error_handler import register_errorhandlers
        register_errorhandlers(app)

        # Jinja env
        set_jinja_env(app)

        app.logger.info("[arasCore] App started.")

    return app


# Expose db for flask db migrate
from .lib.extensions import db  # noqa: E402, F401
