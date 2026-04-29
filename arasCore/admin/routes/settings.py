# -*- coding: utf-8 -*-
"""
arasCore/admin/routes/settings.py
Refactored into modules under settings_modules/
"""
from .settings_modules.core import settings
from .settings_modules.database import db_table_detail, db_generate_view
from .settings_modules.server import settings_upload_save, server_settings_save
from .settings_modules.roles import role_new, role_edit
from .settings_modules.menu import menu_data, menu_save
from .settings_modules.webhooks import webhook_new, webhook_toggle
from .settings_modules.scripts import script_new, script_edit

# Add others as needed or just import the modules to register routes
from .settings_modules import database, server, roles, menu, webhooks, scripts
