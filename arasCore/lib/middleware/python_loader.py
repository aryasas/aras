# -*- coding: utf-8 -*-
"""
arasCore/lib/middleware/python_loader.py
=========================================
PythonLoaderMiddleware — handles Python file/zip upload → app module injection.

Entry points:
  from_zip(file_storage, flask_app) -> dict   (install from .zip upload)
  from_folder(path, flask_app)      -> dict   (install from extracted folder)
  inject_module(app_name, flask_app)          (dynamic blueprint registration)

Folder convention expected inside zip:
    {app_name}/
        __init__.py
        models.py
        forms.py
        views.py        ← must expose app_bp

Current status: PASSTHROUGH
  - Extraction and file placement is implemented.
  - Dynamic blueprint injection is a passthrough (needs server restart).
  - The scaffold generator in installer.py produces compatible files.

Future extension:
  - Hot-reload blueprint without restart (Flask application reload trick)
  - AI-assisted code generation from natural language description
  - Validation: lint models.py, check for security issues before install
  - Sandboxed test run before registering in production context
"""
import os
import zipfile
import logging
import importlib

logger = logging.getLogger(__name__)

# Where installed code-based apps live
APPS_CODE_ROOT = "apps_code"


class PythonLoaderMiddleware:
    """
    Middleware for Python file/zip based app installation.
    Handles extraction, placement, and blueprint registration.
    """

    @staticmethod
    def get_apps_code_root(flask_app) -> str:
        return os.path.join(flask_app.root_path, APPS_CODE_ROOT)

    @staticmethod
    def from_zip(file_storage, flask_app) -> dict:
        """
        Extract a zip containing a Python app module, place it in apps_code/,
        and attempt blueprint registration.

        Also detects a bundled manifest.yaml/yml/json at the zip root or inside
        the app folder and returns it under "definition" for hybrid installs.

        Returns:
          {
            "app_name": str, "path": str, "registered": bool,
            "message": str, "definition": dict|None
          }
        """
        import tempfile, shutil, io

        definition = None

        with tempfile.TemporaryDirectory() as tmp:
            zip_path = os.path.join(tmp, "upload.zip")
            file_storage.save(zip_path)

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(tmp)

                # Look for bundled manifest at root or one level deep
                manifest_names = ["manifest.yaml", "manifest.yml", "manifest.json"]
                for zname in zf.namelist():
                    bname = zname.split("/")[-1].lower()
                    if bname in manifest_names and not zname.endswith("/"):
                        try:
                            from .app_definition import AppDefinitionMiddleware
                            def_bytes = zf.read(zname)
                            if bname.endswith(".json"):
                                definition = AppDefinitionMiddleware.from_json(def_bytes)
                            else:
                                definition = AppDefinitionMiddleware.from_yaml(def_bytes)
                            logger.info(f"[python_loader] bundled manifest found: {zname}")
                        except Exception as e:
                            logger.warning(f"[python_loader] manifest parse failed: {e}")
                        break

            # Find the app folder (first subfolder that has views.py)
            app_name = None
            app_src  = None
            for entry in os.listdir(tmp):
                candidate = os.path.join(tmp, entry)
                if os.path.isdir(candidate) and os.path.isfile(os.path.join(candidate, "views.py")):
                    app_name = entry
                    app_src  = candidate
                    break

            if not app_name:
                raise ValueError("Zip must contain a folder with views.py at the root level.")

            dst_root = PythonLoaderMiddleware.get_apps_code_root(flask_app)
            os.makedirs(dst_root, exist_ok=True)
            dst = os.path.join(dst_root, app_name)

            if os.path.exists(dst):
                raise ValueError(f"App '{app_name}' already installed at {dst}. Remove it first.")

            shutil.copytree(app_src, dst)
            logger.info(f"[python_loader] installed: {app_name} → {dst}")

        registered = PythonLoaderMiddleware.inject_module(app_name, flask_app, dst_root)

        return {
            "app_name":   app_name,
            "path":       dst,
            "registered": registered,
            "definition": definition,
            "message":    (
                f"App '{app_name}' installed. Routes registered live."
                if registered else
                f"App '{app_name}' installed. Restart server to activate routes."
            ),
        }

    @staticmethod
    def from_folder(app_name: str, flask_app) -> dict:
        """
        Register an already-placed app folder from apps_code/.
        Used when manually dropping a folder on the server.
        """
        dst_root   = PythonLoaderMiddleware.get_apps_code_root(flask_app)
        registered = PythonLoaderMiddleware.inject_module(app_name, flask_app, dst_root)
        return {
            "app_name":   app_name,
            "registered": registered,
            "message":    (
                f"App '{app_name}' registered live."
                if registered else
                f"App '{app_name}' placed. Restart server to activate routes."
            ),
        }

    @staticmethod
    def inject_module(app_name: str, flask_app, apps_code_root: str = None) -> bool:
        """
        Dynamically import and register the blueprint from apps_code/{app_name}/views.py.

        Passthrough: Flask does not support removing blueprints at runtime, so
        this only works for NEW apps added without a restart. Existing blueprints
        with the same name cannot be re-registered.

        Returns True if successfully registered, False if restart is needed.
        """
        if apps_code_root is None:
            apps_code_root = PythonLoaderMiddleware.get_apps_code_root(flask_app)

        bp_name = f"code_{app_name}"
        if bp_name in flask_app.blueprints:
            logger.info(f"[python_loader] Blueprint {bp_name} already registered.")
            return True

        # Add apps_code root to sys.path temporarily
        import sys
        if apps_code_root not in sys.path:
            sys.path.insert(0, apps_code_root)

        try:
            mod = importlib.import_module(f"{app_name}.views")
            bp  = getattr(mod, "app_bp", None) or getattr(mod, "bp", None)
            if bp is None:
                logger.warning(f"[python_loader] {app_name}/views.py has no app_bp.")
                return False

            # Rename blueprint to avoid collision with future installs
            bp.name = bp_name
            flask_app.register_blueprint(bp)
            logger.info(f"[python_loader] Registered blueprint: {bp_name}")
            return True

        except Exception as e:
            logger.error(f"[python_loader] Failed to inject {app_name}: {e}", exc_info=True)
            return False
