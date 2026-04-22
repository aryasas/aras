# -*- coding: utf-8 -*-
"""arasCore/arasAdmin/routes/__init__.py — register all admin route sub-modules."""
from flask import g
from flask_login import current_user

from arasCore.arasAdmin import arasAdmin_bp
from arasCore.arasAdmin.models import UserActivity
from arasCore.arasAdmin.services import build_sidebar_menu


@arasAdmin_bp.before_app_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        g.activities = current_user.activities.order_by(UserActivity.created_at.desc())
        g.gmenu = build_sidebar_menu()


from . import dashboard, dev, settings, apps, users  # noqa: F401, E402
