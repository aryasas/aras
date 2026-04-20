from .utils import Utilities as ut
from importlib import import_module

# Blueprint yang di-register manual — exclude dari auto-discover
# app_notes and app_basic still use old app_admin/app_auth imports, skip for now
MANUAL_BLUEPRINTS = ["app_admin", "app_manager", "app_notes", "app_basic"]

def register_blueprints(app):
    # import semua blueprint kecuali yang di-register manual
    for module_name in ut.get_folder("app_", "app_admin"):
        if module_name in MANUAL_BLUEPRINTS:
            continue
        module = import_module("aras.{}.views".format(module_name))
        app.register_blueprint(module.app_bp)

    # import auth (arasCore)
    from arasCore.routes import auth_bp
    app.register_blueprint(auth_bp)

    # import admin (arasCore) — harus paling akhir
    from arasCore.arasAdmin import arasAdmin_bp
    app.register_blueprint(arasAdmin_bp)
