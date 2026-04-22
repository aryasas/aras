import os
import re
import logging
from importlib import import_module

from flask import Blueprint, abort
from flask_login import login_required

logger = logging.getLogger(__name__)

_SKIP = {"app_admin", "app_manager"}

# Registry semua AppHelper dari code-based apps — dibaca oleh build_sidebar_menu()
_helper_registry: dict = {}   # {app_name: AppHelper}


def get_helper_registry() -> dict:
    return dict(_helper_registry)


def _load_manifest(pkg_name: str):
    """
    Coba import {pkg_name}.manifest dan kembalikan AppHelper instance.
    Kembalikan None jika tidak ada atau bukan AppHelper.
    """
    from arasCore.lib.app_helper import AppHelper
    try:
        mod = import_module(f"{pkg_name}.manifest")
        helper = getattr(mod, "helper", None)
        if isinstance(helper, AppHelper):
            return helper
        logger.debug(f"[blueprints] {pkg_name}/manifest.py: tidak punya 'helper' AppHelper")
    except ModuleNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"[blueprints] gagal load manifest {pkg_name}: {e}")
    return None


def _register_helper(flask_app, helper):
    """
    Baca AppHelper dan mount semua routes langsung ke flask_app (bukan blueprint)
    agar URL tidak kena prefix dari blueprint app.

    Routes yang dibuat:
      /api/<app>/<resource>/            — universal CRUD via api_handler
      /api/<app>/<custom_path>/         — custom handlers dari app
      /admin/<app>/<resource>/          — admin list + delete
    """
    from arasCore.lib.api_handler import register_api_model, register_custom_route

    # Buat satu blueprint khusus untuk helper ini (tanpa url_prefix)
    # agar endpoint name tetap unik tanpa konflik dengan blueprint app
    helper_bp = Blueprint(f"_helper_{helper.name}", __name__)

    api_prefix = helper.get_api_prefix()    # /api/<api_slug>
    adm_prefix = helper.get_admin_prefix()  # /admin/<admin_slug>

    # ── 1. Resource CRUD → daftar ke universal API registry ──────────────────
    for res in helper.resources:
        if res.model is None:
            continue  # link-only ResourceDef (custom url, no CRUD)
        url_key = f"{helper.api_slug}/{res.name}"
        register_api_model(
            url_key,
            res.model,
            serializer=res.get_serializer(),
            readonly=res.readonly,
            handler=res.handler,
            searchable=getattr(res, "searchable", []),
            filters=getattr(res, "filters", []),
        )
        logger.debug(f"[blueprints] API resource: /api/{url_key}/")

        if res.admin_list:
            _mount_admin_resource(helper_bp, res, adm_prefix, helper)

    # ── 2. Custom routes → /api/<app>/<path>/ ────────────────────────────────
    for cr in helper.custom_routes:
        rel_path = cr.path.strip("/")
        full_url = f"{api_prefix}/{rel_path}/"
        clean    = re.sub(r"<[^>]+>", "x", rel_path).replace("/", "_")
        ep_name  = f"api_{helper.api_slug}_{clean}"

        handler = login_required(cr.handler) if cr.require_auth else cr.handler

        try:
            helper_bp.add_url_rule(full_url, endpoint=ep_name, view_func=handler, methods=cr.methods)
            register_custom_route(f"{helper.api_slug}/{rel_path}", cr.handler, methods=cr.methods, require_auth=cr.require_auth)
            logger.debug(f"[blueprints] custom API: {full_url}")
        except Exception as e:
            logger.error(f"[blueprints] gagal mount custom route {full_url}: {e}")

    # ── 3. Auto-mount /admin/<admin_slug>/settings/ ────────────────────────────
    try:
        from arasCore.arasAdmin.settings_service import mount_settings_route
        mount_settings_route(
            helper_bp, helper.admin_slug, helper.title,
            schema=getattr(helper, "settings_schema", None) or [],
            is_dynamic=False,
            endpoint=f"settings_{helper.name}",
            registry_key=helper.name,
        )
    except Exception as e:
        logger.warning(f"[blueprints] settings mount failed for {helper.name}: {e}")

    # ── 4. Auto-mount /admin/<admin_slug>/ home page ───────────────────────────
    try:
        from arasCore.arasAdmin.home_service import mount_home_route
        mount_home_route(
            helper_bp, helper.admin_slug, helper.title,
            is_dynamic=False,
            endpoint=f"home_{helper.name}",
            registry_key=helper.name,
        )
    except Exception as e:
        logger.warning(f"[blueprints] home mount failed for {helper.name}: {e}")

    # ── 5. Auto-mount /admin/<admin_slug>/<slug>/ for MenuGroup sub-pages ──────
    if helper.menu_groups:
        try:
            from arasCore.arasAdmin.home_service import mount_group_route
            mount_group_route(
                helper_bp, helper.admin_slug, helper.title,
                endpoint=f"group_{helper.name}",
                registry_key=helper.name,
            )
        except Exception as e:
            logger.warning(f"[blueprints] group mount failed for {helper.name}: {e}")

    @helper_bp.before_request
    def _set_gmenu():
        from flask import g, request as _req
        from flask_login import current_user
        if current_user.is_authenticated and not hasattr(g, "gmenu"):
            from arasCore.arasAdmin.services import build_sidebar_menu
            g.gmenu = build_sidebar_menu()
        # Expose app template for non-admin routes so handlers can render custom layouts
        if not _req.path.startswith("/admin/"):
            g.app_template = getattr(helper, "template", None)

    flask_app.register_blueprint(helper_bp)
    _helper_registry[helper.name] = helper
    logger.debug(f"[blueprints] helper registered: {helper.name}")

    # Auto-sync MenuGroup rows into DB so menu is fully DB-driven
    if helper.menu_groups:
        try:
            from arasCore.lib.extensions import db
            from arasCore.lib.installer import sync_helper_to_db
            with flask_app.app_context():
                sync_helper_to_db(helper, db)
        except Exception as _se:
            logger.debug(f"[blueprints] menu group sync skipped for {helper.name}: {_se}")


def _rbac_check(helper, res, action):
    """Return True if current_user may perform action on resource. Always True when RBAC disabled."""
    from arasCore.rbac import check_permission
    from flask_login import current_user
    return check_permission(current_user, helper.name, res.name, action)


def _mount_admin_resource(bp, res, adm_prefix, helper):
    """Mount CRUD admin routes for one ResourceDef onto blueprint."""
    from arasCore.lib.admin_mount import AdminResourceMounter
    AdminResourceMounter(bp, res, adm_prefix, helper).mount()


def _is_app_enabled(entry: str, aras_pkg: str) -> bool:
    """
    Return True if the app_* package should be loaded.

    Rules (in order):
    1. Package __init__.py sets ARAS_AUTOLOAD = True  → always load (dev/built-in).
    2. AppManagerApp record exists with is_active=True → load (framework-installed).
    3. Otherwise → skip (app exists on disk but not installed/activated).
    """
    # Rule 1: opt-in autoload flag in __init__.py
    init_path = os.path.join(aras_pkg, entry, "__init__.py")
    if os.path.isfile(init_path):
        try:
            with open(init_path) as fh:
                for line in fh:
                    if line.strip().startswith("ARAS_AUTOLOAD"):
                        if "True" in line:
                            return True
                        break  # found the var but it's False/other
        except Exception:
            pass

    # Rule 2: check DB — only possible after configure_database() ran
    app_name = entry[len("app_"):]  # strip "app_" prefix → "soc", "erp", etc.
    try:
        from arasCore.arasAdmin.models import AppManagerApp
        rec = AppManagerApp.query.filter_by(name=app_name, is_active=True).first()
        if rec:
            return True
    except Exception:
        # DB not ready yet (first boot before create_all) — skip DB check
        pass

    return False


def _register_aras_apps(app):
    """
    Auto-discover dan register app_* dari folder aras/.
    Hanya load app yang memenuhi syarat:
      - ARAS_AUTOLOAD = True di __init__.py, ATAU
      - Ada record AppManagerApp dengan is_active=True di DB.
    """
    aras_pkg = os.path.normpath(os.path.join(app.root_path, "..", "aras"))

    if not os.path.isdir(aras_pkg):
        logger.warning(f"[blueprints] aras package not found at: {aras_pkg}")
        return

    for entry in sorted(os.listdir(aras_pkg)):
        if not entry.startswith("app_") or entry in _SKIP:
            continue

        has_views = (
            os.path.isfile(os.path.join(aras_pkg, entry, "views.py")) or
            os.path.isfile(os.path.join(aras_pkg, entry, "views", "__init__.py"))
        )
        has_manifest = os.path.isfile(os.path.join(aras_pkg, entry, "manifest.py"))
        if not has_views and not has_manifest:
            logger.debug(f"[blueprints] skip {entry} — no views.py or manifest.py")
            continue

        if not _is_app_enabled(entry, aras_pkg):
            logger.info(f"[blueprints] skip {entry} — not installed/active in DB (set ARAS_AUTOLOAD=True to override)")
            continue

        pkg_name = f"aras.{entry}"
        try:
            bp = None
            if has_views:
                mod = import_module(f"{pkg_name}.views")
                bp  = getattr(mod, "app_bp", None) or getattr(mod, "bp", None)
                if bp is not None:
                    app.register_blueprint(bp)

            helper = _load_manifest(pkg_name)
            if helper:
                _register_helper(app, helper)
                logger.info(
                    f"[blueprints] registered: {entry} + manifest "
                    f"({len(helper.resources)} resources, {len(helper.custom_routes)} custom routes)"
                )
            elif bp is None:
                logger.warning(f"[blueprints] {pkg_name} has no app_bp and no manifest — skip")
            else:
                logger.info(f"[blueprints] registered: {entry} (no manifest)")

        except Exception as e:
            logger.error(f"[blueprints] failed to load {entry}: {e}", exc_info=True)


def register_app_modules(app):
    """
    Dipanggil dari arasCore.create_app() setelah auth_bp terdaftar.
    Load app_* dari aras/ lalu register arasAdmin terakhir.
    """
    _register_aras_apps(app)

    from arasCore.arasAdmin import arasAdmin_bp
    app.register_blueprint(arasAdmin_bp)
