# -*- coding: utf-8 -*-
from flask import jsonify, g, request, render_template
from flask_login import login_required, current_user
from arasCore.admin import admin_bp
from arasCore.admin.services import build_sidebar_menu
from arasCore.admin.models import ArasSystemSetting, AppManagerTable
from arasCore.lib.services.api_handler import get_api_registry
