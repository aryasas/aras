# gemini-flash
from core.base.app import App
from core.registry.permission_registry import Permission
from .sections import sections
from . import hooks

class CoreConfigApp(App):
    app_name = "core_config"
    app_label = "Workspace"
    icon = "Settings"
    version = "1.0.0"
    required = True
    provides = ["core_config"]
    
    config_sections = sections
    permissions = [
        Permission("config.read", "Read Configuration"),
        Permission("config.write", "Write Configuration"),
        Permission("config.secrets.read", "Read Configuration Secrets"),
    ]

    @classmethod
    def on_install(cls, db, tenant_id):
        hooks.on_install(db, tenant_id)

    @classmethod
    def on_uninstall(cls, db, tenant_id):
        hooks.on_uninstall(db, tenant_id)

    @classmethod
    def seed(cls, db):
        from core.lib.i18n import seed_locale_translations
        seed_locale_translations(db)
