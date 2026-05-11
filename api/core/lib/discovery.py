import importlib
import pkgutil
from typing import List, Type
from fastapi import FastAPI
from .. import Aras

def discover_apps(package_path: str = "api.apps"):
    """
    Otomatis mencari dan mengimpor semua modul di dalam folder apps/
    yang memiliki class turunan dari ArasApp.
    """
    print(f"Discovering apps in {package_path}...")
    try:
        package = importlib.import_module(package_path)
    except ImportError as e:
        print(f"Error importing {package_path}: {e}")
        return

    # Debugging path
    print(f"Package path: {package.__path__}")

    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package_path + "."):
        print(f"Checking module: {module_name}")
        if module_name.endswith(".app"):
            print(f"Found app module: {module_name}")
            importlib.import_module(module_name)

def register_app_routes(app: FastAPI, prefix: str = "/api/v1"):
    """
    Mengambil semua ArasApp yang terdaftar dan mendaftarkan route CRUD untuk setiap modelnya.
    """
    registered_apps = Aras.App._registry

    for app_cls_name, app_cls in registered_apps.items():
        # Instance dari ArasApp (seperti ErpApp)
        aras_app = app_cls
        app_prefix = f"{prefix}/{aras_app.app_name}"

        for model in aras_app.models:
            router = Aras.Router(model)
            app.include_router(router, prefix=app_prefix)
            print(f"Registered route: {app_prefix}/{model.__tablename__}")
