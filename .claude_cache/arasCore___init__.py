# -*- coding: utf-8 -*-
"""arasCore/__init__.py — App factory."""
import os
from flask import Flask
from config import config

from .lib.extensions import register_extensions
from .database import configure_database
from .context import register_context_processors
from .utils import set_jinja_env


def create_app(config_type=None):
    if config_type is None:
        config_type = config.get(
            os.getenv("ARAS_CONFIG", "default"), config["default"]
        )

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

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

        # Admin blueprint (lazy to avoid circular)
        from .arasAdmin import arasAdmin_bp
        app.register_blueprint(arasAdmin_bp)

        # Database — create tables
        configure_database(app)

        # Context processors
        register_context_processors(app)

        # Load dynamic apps from DB
        from .arasAdmin.services import load_all_built_apps
        load_all_built_apps(app)

        # Jinja env
        set_jinja_env(app)

        app.logger.info("[arasCore] App started.")

    return app


# Expose db for flask db migrate
from .lib.extensions import db  # noqa: E402, F401
