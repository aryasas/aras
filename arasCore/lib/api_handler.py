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

from arasCore.lib.extensions import db

logger = logging.getLogger(__name__)

# Registry: {"url_key": model_class | callable}
# url_key = URL path tanpa leading slash, e.g. "soc/posts"
# Value bisa model class (generic CRUD) atau callable (custom handler)
_api_registry: dict = {}

# Custom route registry: {"url_key": {"handler": fn, "methods": [...], "require_auth": bool}}
# Didaftarkan oleh AppHelper.custom_routes — framework yang mount ke /api/
_custom_route_registry: dict = {}


def register_api_model(url_key: str, model_cls, serializer=None, readonly: bool = False, handler=None,
                       searchable: list = None, filters: list = None):
    """
    Daftarkan satu model ke universal API registry.
    url_key:    URL path tanpa leading/trailing slash, e.g. "erp/acc/journal"
    serializer: optional callable(obj) -> dict
    readonly:   jika True, hanya GET yang diizinkan
    handler:    optional SubHandler instance — override CRUD logic per resource
    searchable: column names for ?q= full-text search
    filters:    column names allowed in ?filter[field]=
    """
    key = url_key.strip("/")
    if key not in _api_registry:
        _api_registry[key] = {
            "model":      model_cls,
            "serializer": serializer,
            "readonly":   readonly,
            "handler":    handler,
            "searchable": searchable or [],
            "filters":    filters or [],
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


def get_api_url_for_model(model_cls) -> str | None:
    """Return /api/<key>/ URL string for a registered model class, or None."""
    for key, entry in _api_registry.items():
        if entry.get("model") is model_cls:
            return f"/api/{key}/"
    return None


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

    @api_bp.route("/api/<path:resource_path>/_schema/", methods=["GET"])
    @login_required
    def api_schema(resource_path):
        """GET /api/<app>/<resource>/_schema/ → column/field descriptions."""
        key = resource_path.rstrip("/")
        entry = _api_registry.get(key)
        if entry is None:
            return jsonify({"error": f"Resource '{key}' not found."}), 404
        model = entry["model"]
        cols = []
        for col in model.__table__.columns:
            col_type = str(col.type.__class__.__name__).upper()
            info = {
                "name":     col.name,
                "type":     col_type,
                "required": not col.nullable and col.default is None and not col.primary_key,
                "primary_key": col.primary_key,
            }
            if hasattr(col.type, "length") and col.type.length:
                info["max_length"] = col.type.length
            if col.foreign_keys:
                fk = next(iter(col.foreign_keys))
                info["relation"] = str(fk.target_fullname)
            cols.append(info)
        return jsonify({"resource": key, "columns": cols}), 200

    @api_bp.route("/api/_search/", methods=["GET"])
    @login_required
    def api_global_search():
        """GET /api/_search/?q=foo — global search across all searchable resources."""
        from flask_login import current_user
        q = request.args.get("q", "").strip()
        if not q:
            return jsonify({"results": [], "query": q}), 200
        try:
            from arasCore.lib.search import global_search
            results = global_search(q, user=current_user)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"results": results, "query": q, "total": len(results)}), 200

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
            from arasCore.lib.query import ArasQuery
            base_q = model.query
            if h:
                base_q = h.list(base_q)
            searchable = entry.get("searchable") or []
            filters_allowed = entry.get("filters") or []
            aq = ArasQuery(model, request.args, searchable=searchable, filters=filters_allowed)
            # Run query only for pagination/filter — serialize via handler chain
            q = aq._apply_filters_and_sort(base_q)
            page = max(1, request.args.get("page", 1, type=int))
            per_page = min(max(1, request.args.get("per_page", 50, type=int)), 500)
            pag = q.paginate(page=page, per_page=per_page, error_out=False)
            return jsonify({
                "data": [_serialize(item) for item in pag.items],
                "meta": {
                    "page": pag.page, "per_page": pag.per_page,
                    "total": pag.total, "total_pages": pag.pages,
                    "has_next": pag.has_next, "has_prev": pag.has_prev,
                },
            }), 200

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
            try:
                from arasCore.lib.events import emit_crud
                emit_crud(_app_slug, _res_slug, "created", obj=obj)
            except Exception:
                pass
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
                try:
                    from arasCore.lib.events import emit_crud
                    emit_crud(_app_slug, _res_slug, "updated", obj=obj)
                except Exception:
                    pass
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
            try:
                from arasCore.lib.events import emit_crud
                emit_crud(_app_slug, _res_slug, "deleted", obj=obj)
            except Exception:
                pass
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
