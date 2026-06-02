"""
Purpose: The main Facade and Unified Namespace for the Aras Framework.
Context: Root of the api/core module. Consolidates Levels 1, 2, and 3.
Impact: The primary API surface for framework users.
"""
from typing import Type, List

# 1. Level 1 Base
from .base.aras import Aras as BaseAras

# 2. Level 2 Core Abstractions
from .base.model import Model, SoftModel, Base
from .base.app import App
from .base.field import Field
from .base.validation import Validation
from .base.view import View
from .base.schema import Schema
from .base.service import Service
from .base.router import Router
from .base.auth import Auth
from .manager.manager import Manager

# 3. Registry (Level 3 implementations)
from .registry.app_model import AppModel
from .registry.resource_model import ResourceModel
from .registry.field_model import FieldModel
from .registry.link_model import LinkModel
from .registry.translation_model import TranslationModel
from .registry.dashboard_layout_model import DashboardLayoutModel
from .registry.activity_log import ActivityLog
from .registry.role import Role
from .registry.permission import Permission
from .registry.user_role import UserRole
from .registry.widget_model import WidgetModel
from .registry import views # Ensure registry views are registered

# 4. Managers & Sync
from .manager.sync_manager import SyncManager
from .manager.audit_manager import AuditManager
from .manager.workflow_manager import WorkflowManager

# Register built-in workflow handlers (import triggers registration)
from .logic.handler_registry import HandlerRegistry
from .logic import builtin_handlers as _builtin_handlers  # noqa: F401

# 5. Tiers (lib, logic, api)
from . import lib
from . import logic
from . import api
from . import tenant
from .lib import helpers as helper
from .service_registry import ServiceRegistry

class Aras(BaseAras):
    """
    Unified Aras Namespace.
    Consolidates the hierarchy into a single, clean API.
    """
    
    # Tiered Namespaces
    lib = lib
    logic = logic
    api = api
    tenant = tenant
    helper = helper
    ServiceRegistry = ServiceRegistry

    # Core Abstractions (Level 2)
    Model = Model
    SoftModel = SoftModel
    Base = Base
    App = App
    Field = Field
    View = View
    Schema = Schema
    Column = Field # Alias for backward compatibility
    Validation = Validation
    Manager = Manager
    Service = Service
    
    # Registry Models (Level 3)
    AppModel = AppModel
    ResourceModel = ResourceModel
    FieldModel = FieldModel
    LinkModel = LinkModel
    TranslationModel = TranslationModel
    DashboardLayoutModel = DashboardLayoutModel
    ActivityLog = ActivityLog
    Role = Role
    Permission = Permission
    UserRole = UserRole
    WidgetModel = WidgetModel
    HandlerRegistry = HandlerRegistry

    # Database Layer
    db = lib.database.SessionLocal
    get_db = lib.database.get_db
    engine = lib.database.engine
    
    # Engine Logic
    discover_apps = logic.discovery.discover_apps

    @classmethod
    def get_registered(cls, type_name: str):
        """Returns the in-memory registry for a given framework type (e.g., 'Model', 'App')."""
        target = getattr(cls, type_name, None)
        if target and hasattr(target, "_registry"):
            return target._registry
        return {}

    @classmethod
    def get_all_app_models(cls) -> List[Type['Model']]:
        """
        Collects all SQLAlchemy models from all registered Aras applications.
        """
        all_models = []
        for app_cls in App._registry.values():
            all_models.extend(app_cls.models)
        return all_models

# Attach Specialized Managers
Aras.Manager.Sync = SyncManager
Aras.Manager.Audit = AuditManager
Aras.Manager.Workflow = WorkflowManager

# 6. Delayed Implementation Attachments (Level 3)
from .auth.models import User
from .registry.sys_settings import Settings
from .registry.settings_service import SettingsService
from .registry.master_data_registry import master_data_registry

Aras.User = User
Aras.Settings = SettingsService
Aras.SettingsModel = Settings
Aras.MasterData = master_data_registry

# Deprecated alias (to be removed in 2026-08)
import warnings
Aras.ArasSetting = Settings

Aras.Router = logic.router_factory.RouterFactory.create_router

__all__ = ["Aras"]
