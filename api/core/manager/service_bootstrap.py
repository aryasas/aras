"""
Service Bootstrap for Aras Framework.
Registers app-level services into the ServiceRegistry.
"""
import logging
from core.service_registry import ServiceRegistry

logger = logging.getLogger(__name__)

def register_services():
    """Register all discovered services.

    Each app exposes its own services via App.register_services() (a hook called
    here generically). Core never imports an app — apps push their capabilities
    into ServiceRegistry by key, and core resolves them with ServiceRegistry.get.
    """
    from core.base.app import App

    # App-provided services (inverted: apps register themselves, core just drives)
    for app_cls in App._registry.values():
        try:
            app_cls.register_services()
        except Exception as e:  # an app's optional deps may be absent; keep booting
            logger.warning("register_services failed for %s: %s", getattr(app_cls, "app_name", "?"), e)

    # Core Registry & Managers
    try:
        from core.registry.field_model import FieldModel
        from core.registry.resource_model import ResourceModel
        from core.manager.naming_manager import SeriesManager
        ServiceRegistry.register("FieldModel", FieldModel)
        ServiceRegistry.register("ResourceModel", ResourceModel)
        ServiceRegistry.register("SeriesManager", SeriesManager)
    except ImportError:
        pass

    logger.info("Service registration completed.")
    build_resource_map()

def build_resource_map():
    """Builds a centralized map of database tablenames to their REST API paths."""
    from core.base.app import App as _App
    from core.aras import Aras as _Aras
    
    # 1. Map App Models
    for a in _App._registry.values():
        app_path = a._get_clean_path()
        for m in a.models:
            tablename = getattr(m, "__tablename__", None)
            if not tablename:
                continue
            
            seg = tablename
            full_prefix = f"{a.parent_name}_{a.app_name}_" if a.parent_name and a.app_name else None
            table_prefix = f"{a.table_prefix}_" if a.table_prefix else None
            
            if table_prefix and seg.startswith(f"{table_prefix}_"):
                seg = seg[len(table_prefix)+1:]
            elif table_prefix and seg.startswith(table_prefix):
                seg = seg[len(table_prefix):]
            elif full_prefix and seg.startswith(full_prefix):
                seg = seg[len(full_prefix):]
            elif a.app_name and seg.startswith(f"{a.app_name}_"):
                seg = seg[len(a.app_name)+1:]
            elif a.parent_name and seg.startswith(f"{a.parent_name}_"):
                seg = seg[len(a.parent_name)+1:]
                
            path = f"{app_path}/{seg.replace('_', '-')}".lstrip("/")
            ServiceRegistry.register_resource_path(tablename, path)

    # 2. Map Core Models
    core_models = [
        (_Aras.User, "auth/users"),
        (_Aras.Role, "admin/roles"),
        (_Aras.Permission, "admin/permissions"),
        (_Aras.ActivityLog, "admin/activity-log"),
        (_Aras.SettingsModel, "settings"),
        (_Aras.AppModel, "registry/apps"),
        (_Aras.ResourceModel, "registry/resources"),
        (_Aras.FieldModel, "registry/fields"),
        (_Aras.LinkModel, "registry/links"),
        (_Aras.TranslationModel, "registry/translations"),
        (_Aras.WidgetModel, "registry/widgets"),
        (_Aras.DashboardLayoutModel, "registry/dashboard-layouts"),
    ]
    for model, path in core_models:
        if hasattr(model, "__tablename__"):
            ServiceRegistry.register_resource_path(model.__tablename__, path)
    
    logger.info("Resource path map built.")
