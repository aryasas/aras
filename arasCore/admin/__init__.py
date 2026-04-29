# -*- coding: utf-8 -*-
"""arasCore/admin/__init__.py — Admin blueprint."""
from flask import Blueprint

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
)

from . import models  # noqa: F401 — register all models with SQLAlchemy
from . import routes  # noqa: F401, E402
