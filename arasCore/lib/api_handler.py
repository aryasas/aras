# -*- coding: utf-8 -*-
"""
arasCore/lib/api_handler.py
===========================
Universal API handler yang otomatis memberikan endpoint API untuk setiap
app yang terdaftar di arasCore — baik code-based (register_module) maupun
dynamic/built apps (AppManagerApp).

Mendaftarkan:
  GET  /api/                          → daftar semua API endpoint
  GET  /api/<app>/<resource>/         → list + POST
  GET  /api/<app>/<resource>/<id>/    → get, PUT, DELETE satu record

Cara pakai (di create_app, setelah semua blueprint terdaftar):
    from arasCore.lib.api_handler import register_universal_api
    register_universal_api(app)
"""
import logging
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from sqlalchemy.exc import SQLAlchemyError

from arasCore.lib.db import db

logger = logging.getLogger(__name__)

# Registry: {"url_key": model_class | callable}
# url_key = URL path tanpa leading slash, e.g. "soc/posts"
# Value bisa model class (generic CRUD) atau callable (custom handler)
_api_registry: dict = {}

# Custom route registry: {"url_key": {"handler": fn, "methods": [...], "require_auth": bool}}
# Didaftarkan oleh AppHelper.custom_routes — framework yang mount ke /api/
_custom_route_registry: dict = {}


def register_api_model(url_key: str, model_cls, serializer=None, readonly: bool = False, handler=None):
    """
    Daftarkan satu model ke universal API registry.
    url_key:    URL path tanpa leading/trailing slash, e.g. "erp/acc/journal"
    serializer: optional callable(obj) -> dict
    readonly:   jika True, hanya GET yang diizinkan
    handler:    optional SubHandler instance — override CRUD logic per resource
    """
    key = url_key.strip("/")
    if key not in _api_registry:
        _api_registry[key] = {
            "model":      model_cls,
            "serializer": serializer,
            "readonly":   readonly,
            "handler":    handler,
        }
        logger.debug(f"[api_handler] registered: /api/{key}/")


def register_custom_route(url_key: str, handler: callable, methods: list = None, require_auth: bool = True):
    """
    Daftarkan custom route handler ke registry.
    url_key: path relatif dari /api/, e.g. "soc/feed"
    Dipanggil oleh blueprints.py saat membaca AppHelper.custom_routes.
    """
    key = url_key.strip("/")
    if key not in _custom_route_registry:
        _custom_route_registry[key] = {
            "handler": handler,
            "methods": methods or ["GET"],
            "require_auth": require_auth,
        }
        logger.debug(f"[api_handler] custom route: /api/{key}/")


def get_api_registry() -> dict:
    return dict(_api_registry)


def _row_to_dict(obj) -> dict:
    # Prefer model's own to_dict() (ArasModel subclasses define this)
    if hasattr(obj, "to_dict") and callable(obj.to_dict):
        return obj.to_dict()
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}


def _match_custom_route(pattern: str, key: str) -> dict | None:
    """Match a URL key against a custom route pattern with <int:name> or <name> segments.
    Returns a dict of captured kwargs if matched, or None."""
    import re
    int_params = set(re.findall(r"<int:(\w+)>", pattern))
    # Replace all segments in one pass to avoid double-substitution
    def _seg(m):
        name = m.group(2) or m.group(3)
        digits_only = m.group(1) == "int:"
        return f"(?P<{name}>{'[0-9]+' if digits_only else '[^/]+'})"
    regex = re.sub(r"<(int:)?(\w+)>", _seg, pattern)
    match = re.fullmatch(regex, key)
    if match is None:
        return None
    result = {}
    for k, v in match.groupdict().items():
        result[k] = int(v) if k in int_params else v
    return result


def _build_api_blueprint() -> Blueprint:
    api_bp = Blueprint("aras_api", __name__)

    @api_bp.route("/api/")
    def api_index():
        """Discovery endpoint — list semua API yang tersedia."""
        base = request.host_url.rstrip("/")
        endpoints = []
        for key in sorted(_api_registry.keys()):
            entry = _api_registry[key]
            model = entry["model"]
            readonly = entry.get("readonly", False)
            methods = ["GET"] if readonly else ["GET", "POST", "PUT", "DELETE"]
            endpoints.append({
                "resource":   key,
                "collection": f"{base}/api/{key}/",
                "item":       f"{base}/api/{key}/{{id}}/",
                "methods":    methods,
                "type":       "crud",
            })
        for key in sorted(_custom_route_registry.keys()):
            endpoints.append({
                "resource": key,
                "url":      f"{base}/api/{key}/",
                "methods":  _custom_route_registry[key]["methods"],
                "type":     "custom",
            })
        return jsonify({
            "api_version": "1.0",
            "endpoints":   endpoints,
            "total":       len(endpoints),
        }), 200

    @api_bp.route("/api/<path:resource_path>/", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    @login_required
    def api_collection(resource_path):
        """GET /api/<app>/<resource>/ → list | POST → create; also dispatches custom routes"""
        key = resource_path.rstrip("/")

        # Dispatch custom routes first (they may contain path params like session/<id>/products)
        for pattern, creg in _custom_route_registry.items():
            matched = _match_custom_route(pattern, key)
            if matched is not None:
                if request.method not in creg["methods"]:
                    return jsonify({"error": "Method not allowed"}), 405
                return creg["handler"](**matched)

        entry = _api_registry.get(key)
        if entry is None:
            return jsonify({"error": f"Resource '{key}' not found."}), 404

        # RBAC enforcement
        _app_slug, _res_slug = (key.split("/", 1) + [None])[:2]
        _action_map = {"GET": "view", "POST": "create"}
        _action = _action_map.get(request.method, "view")
        from arasCore.rbac import check_permission
        if not check_permission(current_user, _app_slug, _res_slug, _action):
            return jsonify({"error": "Forbidden"}), 403

        model    = entry["model"]
        h        = entry.get("handler")
        readonly = entry.get("readonly", False)

        # Serializer: handler.serialize > entry.serializer > default
        def _serialize(obj):
            if h:
                s = h.serialize(obj)
                if s is not None:
                    return s
            fn = entry.get("serializer")
            return fn(obj) if fn else _row_to_dict(obj)

        if request.method == "GET":
            q = model.query
            if h:
                q = h.list(q)
            return jsonify([_serialize(i) for i in q.all()]), 200

        if readonly:
            return jsonify({"error": "This resource is read-only."}), 405

        data = request.get_json(force=True, silent=True) or {}
        if not data:
            return jsonify({"error": "No JSON body provided."}), 400
        try:
            user_id = getattr(current_user, "id", None)
            if hasattr(model, "create") and callable(model.create):
                # ArasModel path: handler hooks invoked inside create()
                obj = model()
                _SKIP = {"id", "created_at", "updated_at", "created_by_id", "updated_by_id", "deleted_at"}
                for col in obj.__table__.columns:
                    if col.name not in _SKIP and col.name in data:
                        setattr(obj, col.name, data[col.name])
                if h:
                    h.before_create(data, obj)
                if user_id:
                    obj.created_by_id = user_id
                    obj.updated_by_id = user_id
                obj.before_save(is_new=True)
                db.session.add(obj)
                db.session.commit()
                obj.after_save(is_new=True)
                if h:
                    h.after_create(obj)
                    db.session.commit()
            else:
                obj = model()
                for col in obj.__table__.columns:
                    if col.name != "id" and col.name in data:
                        setattr(obj, col.name, data[col.name])
                if h:
                    h.before_create(data, obj)
                db.session.add(obj)
                db.session.commit()
                if h:
                    h.after_create(obj)
                    db.session.commit()
            return jsonify(_serialize(obj)), 201
        except (SQLAlchemyError, ValueError, Exception) as ex:
            db.session.rollback()
            logger.error(f"[api_handler] POST error: {ex}")
            return jsonify({"error": str(ex)}), 500

    @api_bp.route("/api/<path:resource_path>/<int:item_id>/", methods=["GET", "PUT", "DELETE"])
    @login_required
    def api_item(resource_path, item_id):
        """GET /api/<app>/<resource>/<id>/ | PUT → update | DELETE → hapus"""
        key = resource_path.rstrip("/")
        entry = _api_registry.get(key)
        if entry is None:
            return jsonify({"error": f"Resource '{key}' not found."}), 404

        # RBAC enforcement
        _app_slug, _res_slug = (key.split("/", 1) + [None])[:2]
        _action_map = {"GET": "view", "PUT": "edit", "DELETE": "delete"}
        _action = _action_map.get(request.method, "view")
        from arasCore.rbac import check_permission
        if not check_permission(current_user, _app_slug, _res_slug, _action):
            return jsonify({"error": "Forbidden"}), 403

        model    = entry["model"]
        h        = entry.get("handler")
        readonly = entry.get("readonly", False)
        obj      = model.query.get_or_404(item_id)

        def _serialize(obj):
            if h:
                s = h.serialize(obj)
                if s is not None:
                    return s
            fn = entry.get("serializer")
            return fn(obj) if fn else _row_to_dict(obj)

        if request.method == "GET":
            return jsonify(_serialize(obj)), 200

        if readonly:
            return jsonify({"error": "This resource is read-only."}), 405

        if request.method == "PUT":
            data = request.get_json(force=True, silent=True) or {}
            if not data:
                return jsonify({"error": "No JSON body provided."}), 400
            try:
                user_id = getattr(current_user, "id", None)
                if h:
                    h.before_update(data, obj)
                if hasattr(obj, "update_self") and callable(obj.update_self):
                    obj.update_self(data, user_id=user_id)
                else:
                    for col in obj.__table__.columns:
                        if col.name != "id" and col.name in data:
                            setattr(obj, col.name, data[col.name])
                    db.session.commit()
                if h:
                    h.after_update(obj)
                    db.session.commit()
                return jsonify(_serialize(obj)), 200
            except (SQLAlchemyError, ValueError, Exception) as ex:
                db.session.rollback()
                return jsonify({"error": str(ex)}), 500

        # DELETE
        try:
            if h:
                h.before_delete(obj)
            if hasattr(obj, "delete_self") and callable(obj.delete_self):
                user_id = getattr(current_user, "id", None)
                obj.delete_self(user_id=user_id)
            else:
                db.session.delete(obj)
                db.session.commit()
            return jsonify({"message": "Deleted."}), 200
        except (SQLAlchemyError, ValueError, Exception) as ex:
            db.session.rollback()
            return jsonify({"error": str(ex)}), 500

    return api_bp


def _auto_register_core_models():
    """Auto-register model arasCore ke registry."""
    from arasCore.auth import User
    from arasCore.permissions import Role, Permission
    from arasCore.arasAdmin.models import (
        Notification, UserActivity,
        AppManagerApp, AppManagerTable, AppManagerColumn,
    )
    _CORE = [
        ("admin/users",               User),
        ("admin/notifications",       Notification),
        ("admin/activities",          UserActivity),
        ("admin/apps",                AppManagerApp),
        ("admin/apps/tables",         AppManagerTable),
        ("admin/apps/tables/columns", AppManagerColumn),
        ("admin/roles",               Role),
        ("admin/permissions",         Permission),
    ]
    for key, model in _CORE:
        try:
            register_api_model(key, model)
        except Exception as e:
            logger.warning(f"[api_handler] skip {key}: {e}")


def register_universal_api(flask_app):
    """
    Daftarkan universal API blueprint ke Flask app.
    Harus dipanggil di create_app() setelah semua blueprint lain terdaftar
    agar _api_registry sudah terisi.
    """
    _auto_register_core_models()
    bp = _build_api_blueprint()
    flask_app.register_blueprint(bp)
    logger.info(f"[api_handler] Universal API registered. {len(_api_registry)} resource(s) available.")
