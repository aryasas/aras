# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/page_actions.py
Registry + dispatch blueprint for AppManagerPageAction buttons.

Usage (app code):
    from arasCore.arasAdmin.page_actions import register_action

    @register_action("my_action")
    def handle_my_action(record_id, table_name, **kw):
        # do work
        return {"status": "ok", "message": "Done"}
"""
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required

logger = logging.getLogger(__name__)

_ACTION_REGISTRY: dict = {}


def register_action(name: str):
    """Decorator to register a page-action handler by name."""
    def decorator(fn):
        _ACTION_REGISTRY[name] = fn
        logger.debug(f"[page_actions] registered action: {name!r}")
        return fn
    return decorator


def get_actions_for_table(table_id: int, visibility: str = "list") -> list:
    """Return serialized action dicts for a table + visibility context."""
    try:
        from arasCore.arasAdmin.models import AppManagerPageAction
        rows = (
            AppManagerPageAction.query
            .filter_by(table_id=table_id, is_active=True)
            .filter(AppManagerPageAction.visibility.in_([visibility, "both"]))
            .order_by(AppManagerPageAction.order)
            .all()
        )
        return [r.to_dict() for r in rows]
    except Exception as e:
        logger.warning(f"[page_actions] get_actions_for_table failed: {e}")
        return []


def _build_actions_blueprint() -> Blueprint:
    bp = Blueprint("aras_actions", __name__)

    @bp.route("/admin/actions/dispatch/", methods=["POST"])
    @login_required
    def dispatch():
        data = request.get_json(force=True, silent=True) or {}
        if not data:
            data = request.form.to_dict()
        handler_name = (data.get("handler_name") or "").strip()
        record_id    = data.get("record_id")
        table_name   = (data.get("table_name") or "").strip()

        fn = _ACTION_REGISTRY.get(handler_name)
        if not fn:
            return jsonify({"error": f"Unknown action: {handler_name!r}"}), 404
        try:
            result = fn(
                record_id=int(record_id) if record_id else None,
                table_name=table_name,
            )
            return jsonify(result if isinstance(result, dict) else {"status": "ok"}), 200
        except Exception as e:
            logger.error(f"[page_actions] dispatch error for {handler_name!r}: {e}")
            return jsonify({"error": str(e)}), 500

    return bp


def register_actions_blueprint(flask_app):
    """Register the dispatch blueprint. Call once in create_app()."""
    flask_app.register_blueprint(_build_actions_blueprint())
    logger.info("[page_actions] dispatch blueprint registered at /admin/actions/dispatch/")
