# -*- coding: utf-8 -*-
"""arasCore/admin/routes/__init__.py — register all admin route sub-modules."""
from flask import g
from flask_login import current_user

from arasCore.admin import admin_bp
from arasCore.admin.models import UserActivity
from arasCore.admin.services import build_sidebar_menu


@admin_bp.before_app_request
def before_request():
    g.user = current_user
    if current_user.is_authenticated:
        g.activities = current_user.activities.order_by(UserActivity.created_at.desc())
        g.gmenu = build_sidebar_menu()


from . import dashboard, dev, settings, apps, users, help  # noqa: F401, E402
