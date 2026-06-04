# gemini-flash
from core.base.app import App
from core.registry.permission_registry import Permission
from .sections import sections
from . import hooks
from .workflow import WorkflowTemplate, WorkflowState, WorkflowTransition, WorkflowAction
from .models import Organization, Currency, PrintTemplate, Notification
from .config_router import config_router

class CoreConfigApp(App):
    app_name = "core_config"
    app_type = "framework"
    app_label = "Workspace"
    icon = "Settings"
    version = "1.0.0"
    required = True
    provides = ["core_config"]

    routers = [config_router]

    # Framework workflow engine + workspace primitives (relocated from settings).
    models = [
        WorkflowTemplate, WorkflowState, WorkflowTransition, WorkflowAction,
        Organization, Currency, PrintTemplate, Notification,
    ]

    config_sections = sections
    permissions = [
        Permission("config.read", "Read Configuration"),
        Permission("config.write", "Write Configuration"),
        Permission("config.secrets.read", "Read Configuration Secrets"),
    ]

    # claude-opus-4-8
    @classmethod
    def register_services(cls):
        from core.service_registry import ServiceRegistry
        ServiceRegistry.register("WorkflowTemplate", WorkflowTemplate)
        ServiceRegistry.register("WorkflowTransition", WorkflowTransition)
        ServiceRegistry.register("WorkflowState", WorkflowState)
        ServiceRegistry.register("Organization", Organization)
        ServiceRegistry.register("Currency", Currency)
        ServiceRegistry.register("Notification", Notification)
        ServiceRegistry.register("PrintTemplate", PrintTemplate)

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
