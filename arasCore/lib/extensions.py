# -*- coding: utf-8 -*-
"""
arasCore/extensions.py
Flask extensions — single source of truth.
Import from here everywhere, never re-instantiate.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_caching import Cache
from flask_debugtoolbar import DebugToolbarExtension
from flask_migrate import Migrate
from flask_moment import Moment

db           = SQLAlchemy()
login_manager = LoginManager()
csrf         = CSRFProtect()
mail         = Mail()
ma           = Marshmallow()
cache        = Cache()
migrate      = Migrate()
moment       = Moment()
debug_toolbar = DebugToolbarExtension()

EXTENSIONS = [db, login_manager, csrf, mail, ma, cache, moment, debug_toolbar]

def register_extensions(app):
    for ext in EXTENSIONS:
        if ext is migrate:
            ext.init_app(app, db)
        else:
            ext.init_app(app)
    # Set login redirect endpoint
    login_manager.login_view = app.config.get("LOGIN_VIEW", "auth.login_view")
    login_manager.login_message_category = "warning"
