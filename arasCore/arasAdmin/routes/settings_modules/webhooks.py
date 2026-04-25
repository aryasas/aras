# -*- coding: utf-8 -*-
from flask import request, redirect, url_for, flash, jsonify
from flask_login import login_required
from arasCore.arasAdmin import arasAdmin_bp
from arasCore.lib.extensions import db

@arasAdmin_bp.route("/settings/webhooks/new", methods=["POST"])
@login_required
def webhook_new():
    from arasCore.lib.webhook_models import WebhookEndpoint
    d = request.form
    ep = WebhookEndpoint(
        name=d.get("name", ""), url=d.get("url", ""),
        event=d.get("event", "*"), secret=d.get("secret") or None,
        active=True,
    )
    db.session.add(ep)
    db.session.commit()
    flash("Webhook created.", "success")
    return redirect(url_for("admin.settings") + "#panel-webhooks")

@arasAdmin_bp.route("/settings/webhooks/<int:ep_id>/toggle", methods=["POST"])
@login_required
def webhook_toggle(ep_id):
    from arasCore.lib.webhook_models import WebhookEndpoint
    ep = db.session.get(WebhookEndpoint, ep_id)
    if ep:
        ep.active = not ep.active
        db.session.commit()
    return jsonify({"ok": True, "active": ep.active if ep else False})
