import importlib
import pkgutil
from typing import List, Type
from fastapi import FastAPI

from ..base.app import App
from ..logic.router_factory import RouterFactory
from ..logic.integrity_checker import IntegrityChecker

def discover_apps(package_path: str = "apps"):
    """
    Otomatis mencari dan mengimpor semua modul di dalam folder apps/
    yang memiliki class turunan dari App.
    """
    print(f"Discovering apps in {package_path}...")
    try:
        package = importlib.import_module(package_path)
    except ImportError as e:
        print(f"Error importing {package_path}: {e}")
        return

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package_path + "."):
        # Import every module in the app package to ensure full registry and integrity check
        module = importlib.import_module(module_name)
        
        # Enforce Mandatory Aras Inheritance
        IntegrityChecker.check_module(module)


def register_app_routes(app: FastAPI, prefix: str = "/api/v1"):
    """
    Mengambil semua App yang terdaftar dan mendaftarkan route CRUD untuk setiap modelnya.
    """
    registered_apps = App._registry

    for app_cls_name, app_cls in registered_apps.items():
        app_prefix = f"{prefix}/{app_cls.app_name}"

        for model in app_cls.models:
            router = RouterFactory.create_router(model)
            app.include_router(router, prefix=app_prefix)
            print(f"Registered route: {app_prefix}/{model.__tablename__}")

def load_class(class_path: str):
    """
    Dynamically loads a class from a string path (e.g., 'core.registry.naming_series.NamingSeries').
    """
    try:
        module_path, class_name = class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError, ValueError) as e:
        print(f"Error loading class {class_path}: {e}")
        return None
