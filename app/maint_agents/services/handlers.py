"""HTTP handlers for /api/maint_agents/* endpoints."""
from flask import request, jsonify, abort
from flask_login import current_user

from arasCore.lib.agent_runtime import is_dev_mode
from app.maint_agents.agents import doc_sync, form_layout


def _guard():
    if not is_dev_mode():
        abort(403, "maint_agents disabled outside ARAS_MODE=development")
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        abort(403, "admin only")


def _payload(field: str) -> str:
    data = request.get_json(silent=True) or request.form
    val = data.get(field)
    if not val:
        abort(400, f"missing field: {field}")
    return val


def handle_doc_sync():
    _guard()
    return jsonify({"diff": doc_sync.run(_payload("file"))})


def handle_form_layout():
    _guard()
    return jsonify({"layout": form_layout.run(_payload("model"))})
