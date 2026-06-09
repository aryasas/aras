import importlib
import pkgutil
import logging
from typing import List, Type
from fastapi import FastAPI

from ..base.app import App
from ..logic.router_factory import RouterFactory
from ..logic.integrity_checker import IntegrityChecker

# gemini-flash
logger = logging.getLogger(__name__)

def autodiscover_models(package_name: str, module_names: list[str]) -> list:
    """
    Auto-discovers subclasses of Aras.Model within specified modules of a package.
    """
    from ..base.model import Model as ArasModel
    # If called with __name__ from app.py, strip trailing ".app"
    if package_name.endswith(".app"):
        package_name = package_name[:-4]
    discovered_models = []
    for mod_name in module_names:
        full_module_name = f"{package_name}.{mod_name}"
        try:
            module = importlib.import_module(full_module_name)
            for name in dir(module):
                obj = getattr(module, name)
                if (isinstance(obj, type) and
                        issubclass(obj, ArasModel) and
                        obj is not ArasModel and
                        obj.__module__ == full_module_name):
                    discovered_models.append(obj)
        except ImportError as e:
            logger.error(f"Error importing module {full_module_name}: {e}")
    return discovered_models

# claude-opus-4-8
# Framework-tier apps live in core/ (not apps/) and ship with the framework
# regardless of which products are installed. They are registered explicitly,
# never via product discovery (which only scans apps/).
FRAMEWORK_APP_MODULES = [
    "core.workspace",
    "core.settings",
]


# claude-opus-4-8
def register_framework_apps():
    """Import core/ framework apps so their App subclasses enter App._registry.

    Must run BEFORE discover_apps() so framework config sections / required apps
    are present even when zero product apps are installed.
    """
    for module_name in FRAMEWORK_APP_MODULES:
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            logger.error(f"Error importing framework app {module_name}: {e}")


def discover_apps(package_path: str = "apps"):
    """
    Otomatis mencari dan mengimpor semua modul di dalam folder apps/
    yang memiliki class turunan dari App.
    """
    register_framework_apps()
    logger.info(f"Discovering apps in {package_path}...")
    try:
        package = importlib.import_module(package_path)
    except ImportError as e:
        logger.error(f"Error importing {package_path}: {e}")
        return

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package_path + "."):
        # gemini-pro: skip tests during discovery
        if ".tests." in module_name or module_name.split(".")[-1].startswith("test_"):
            continue
            
        # Import every module in the app package to ensure full registry and integrity check
        module = importlib.import_module(module_name)
        
        # Skip router files — they may contain Pydantic schemas that don't inherit from Aras
        if not module_name.endswith("_router"):
            IntegrityChecker.check_module(module)


def resolve_resource_path(tablename: str):
    """
    Map a SQLAlchemy __tablename__ to its registered REST path
    (e.g. 'erp_stock_movements' -> 'erp/stock/movements').
    Returns None if no app owns the model.
    """
    if not tablename:
        return None
    for app_cls in App._registry.values():
        for model in app_cls.models:
            if getattr(model, "__tablename__", None) != tablename:
                continue
            model_seg = tablename
            full_prefix = f"{app_cls.parent_name}_{app_cls.app_name}_" if app_cls.parent_name and app_cls.app_name else None
            if app_cls.table_prefix and model_seg.startswith(f"{app_cls.table_prefix}_"):
                model_seg = model_seg[len(app_cls.table_prefix) + 1:]
            elif full_prefix and model_seg.startswith(full_prefix):
                model_seg = model_seg[len(full_prefix):]
            elif app_cls.app_name and model_seg.startswith(f"{app_cls.app_name}_"):
                model_seg = model_seg[len(app_cls.app_name) + 1:]
            elif app_cls.parent_name and model_seg.startswith(f"{app_cls.parent_name}_"):
                model_seg = model_seg[len(app_cls.parent_name) + 1:]
            return f"{app_cls._get_clean_path().lstrip('/')}/{model_seg.replace('_', '-')}"
    return None


def register_app_routes(app: FastAPI, prefix: str = "/api/v1"):
    """
    Mengambil semua App yang terdaftar dan mendaftarkan route CRUD untuk setiap modelnya.
    """
    registered_apps = App._registry

    for app_cls_name, app_cls in registered_apps.items():
        # Hierarchical App Prefix (e.g., /api/v1/accounting)
        app_clean_path = app_cls._get_clean_path()
        app_prefix = f"{prefix}{app_clean_path}"
        route_count = 0
        custom_count = 0

        for model in app_cls.models:
            if not hasattr(model, "__tablename__"):
                continue
                
            # Clean Model Path (e.g., /accounts)
            model_seg = model.__tablename__
            full_prefix = f"{app_cls.parent_name}_{app_cls.app_name}_" if app_cls.parent_name and app_cls.app_name else None
            if app_cls.table_prefix and model_seg.startswith(f"{app_cls.table_prefix}_"):
                model_seg = model_seg[len(app_cls.table_prefix)+1:]
            elif full_prefix and model_seg.startswith(full_prefix):
                model_seg = model_seg[len(full_prefix):]
            elif app_cls.app_name and model_seg.startswith(f"{app_cls.app_name}_"):
                model_seg = model_seg[len(app_cls.app_name)+1:]
            elif app_cls.parent_name and model_seg.startswith(f"{app_cls.parent_name}_"):
                model_seg = model_seg[len(app_cls.parent_name)+1:]
            
            model_path = f"/{model_seg.replace('_', '-')}"
            
            router = RouterFactory.create_router(model, prefix=model_path)
            app.include_router(router, prefix=app_prefix)
            route_count += 1
            logger.debug(f"Registered route: {app_prefix}{model_path}")

        # Include custom routers defined directly in the App class
        if hasattr(app_cls, 'routers') and isinstance(app_cls.routers, list):
            for custom_router in app_cls.routers:
                # Custom routers are expected to have their own prefix defined internally
                # or we can apply the app_prefix to them. Let's apply the app_prefix for consistency.
                app.include_router(custom_router, prefix=app_prefix)
                custom_count += 1
                logger.debug(f"Registered custom router for app {app_cls.app_name} at prefix: {app_prefix}")

        if route_count or custom_count:
            extra = f" (+{custom_count} custom)" if custom_count else ""
            logger.info(f"{app_cls.app_name}: {route_count} routes{extra} at {app_prefix}")

def load_class(class_path: str):
    """
    Dynamically loads a class from a string path (e.g., 'core.registry.series.Series').
    """
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError, ValueError) as e:
        logger.error(f"Error loading class {class_path}: {e}")
        return None
