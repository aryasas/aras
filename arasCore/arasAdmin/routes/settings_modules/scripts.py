# -*- coding: utf-8 -*-
from flask import request, redirect, url_for, flash, jsonify
from flask_login import login_required
from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db

@arasAdmin_bp.route("/settings/scripts/new", methods=["POST"])
@login_required
def script_new():
    from arasCore.lib.script_models import SrvScript
    d = request.form
    sc = SrvScript(
        name=d.get("name", ""), app=d.get("app", ""),
        resource=d.get("resource", ""), event=d.get("event", "before_insert"),
        code=d.get("code", ""), active=True,
    )
    db.session.add(sc)
    db.session.commit()
    flash("Script created.", "success")
    return redirect(url_for("admin.settings") + "#panel-scripts")

@arasAdmin_bp.route("/settings/scripts/<int:sc_id>/edit", methods=["POST"])
@login_required
def script_edit(sc_id):
    from arasCore.lib.script_models import SrvScript
    sc = db.session.get(SrvScript, sc_id)
    if not sc: return jsonify({"error": "Not found"}), 404
    d = request.get_json(force=True, silent=True) or {}
    for field in ("name", "app", "resource", "event", "code", "active"):
        if field in d: setattr(sc, field, d[field])
    db.session.commit()
    return jsonify({"ok": True})
