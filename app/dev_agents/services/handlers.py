"""HTTP handlers for /api/dev_agents/* endpoints."""
from flask import request, jsonify, abort
from flask_login import current_user

from arasCore.lib.agent_runtime import is_dev_mode
from app.dev_agents.agents import uiux, coder, reviewer


def _guard():
    """Reject if not dev mode or not admin."""
    if not is_dev_mode():
        abort(403, "dev_agents disabled outside ARAS_MODE=development")
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        abort(403, "admin only")


def _payload(field: str) -> str:
    data = request.get_json(silent=True) or request.form
    val = data.get(field)
    if not val:
        abort(400, f"missing field: {field}")
    return val


def handle_uiux():
    _guard()
    return jsonify({"spec": uiux.run(_payload("feature"))})


def handle_coder():
    _guard()
    spec = _payload("spec")
    prev = (request.get_json(silent=True) or request.form).get("previous_code")
    return jsonify({"output": coder.run(spec, prev)})


def handle_reviewer():
    _guard()
    data = request.get_json(silent=True) or request.form
    spec = _payload("spec")
    paths = data.get("paths") or []
    if isinstance(paths, str):
        paths = [paths]
    return jsonify({"review": reviewer.run(spec, paths)})


def handle_pipeline():
    """Run uiux → coder → reviewer in sequence. Single feature → reviewed code."""
    _guard()
    feature = _payload("feature")
    spec = uiux.run(feature)
    code = coder.run(spec)
    review = reviewer.run(spec, [])
    return jsonify({"spec": spec, "code": code, "review": review})
