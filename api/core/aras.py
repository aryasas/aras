"""
Purpose: The main Facade and Unified Namespace for the Aras Framework.
Context: Root of the api/core module. Consolidates Levels 1, 2, and 3.
Impact: The primary API surface for framework users.
"""
from typing import Type

# 1. Level 1 Base
from .base.aras import Aras as BaseAras

# 2. Level 2 Core Abstractions
from .base.model import Model, SoftModel, Base
from .base.app import App
from .base.field import Field
from .base.validation import Validation
from .manager.manager import Manager

# 3. Registry (Level 3 implementations)
from .registry.app_model import AppModel
from .registry.resource_model import ResourceModel
from .registry.field_model import FieldModel
from .registry.link_model import LinkModel
from .registry.translation_model import TranslationModel
from .registry.activity_log import ActivityLog
from .registry.role import Role
from .registry.permission import Permission
from .registry.user_role import UserRole

# 4. Managers & Sync
from .manager.sync_manager import SyncManager
from .manager.audit_manager import AuditManager
from .manager.workflow_manager import WorkflowManager

# 5. Utilities & Libraries
from .lib.database import SessionLocal, get_db, engine
from .lib.discovery import discover_apps

class Aras(BaseAras):
    """
    Unified Aras Namespace.
    Consolidates the hierarchy into a single, clean API.
    """
    
    # Core Abstractions (Level 2)
    Model = Model
    SoftModel = SoftModel
    Base = Base
    App = App
    Field = Field
    Column = Field # Alias for backward compatibility
    Validation = Validation
    Manager = Manager
    
    # Registry Models (Level 3)
    AppModel = AppModel
    ResourceModel = ResourceModel
    FieldModel = FieldModel
    LinkModel = LinkModel
    TranslationModel = TranslationModel
    ActivityLog = ActivityLog
    Role = Role
    Permission = Permission
    UserRole = UserRole
    
    # Database Layer
    db = SessionLocal
    get_db = get_db
    engine = engine
    
    # Logic
    discover_apps = discover_apps

    @classmethod
    def get_registered(cls, type_name: str):
        """Returns the in-memory registry for a given framework type (e.g., 'Model', 'App')."""
        target = getattr(cls, type_name, None)
        if target and hasattr(target, "_registry"):
            return target._registry
        return {}

# Attach Specialized Managers
Aras.Manager.Sync = SyncManager
Aras.Manager.Audit = AuditManager
Aras.Manager.Workflow = WorkflowManager

# 6. Delayed Implementation Attachments (Level 3)
from .auth.models import User
from .registry.sys_settings import ArasSetting
from .lib.router_factory import RouterFactory

Aras.User = User
Aras.ArasSetting = ArasSetting
Aras.Router = RouterFactory.create_router

__all__ = ["Aras"]
