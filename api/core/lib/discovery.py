import importlib
import pkgutil
from typing import List, Type
from fastapi import FastAPI

from ..base.app import App
from ..lib.router_factory import RouterFactory

def discover_apps(package_path: str = "api.apps"):
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
        if module_name.endswith(".app"):
            importlib.import_module(module_name)

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
