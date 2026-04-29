# -*- coding: utf-8 -*-
import os
import json as _json
from flask import request, redirect, url_for, flash, current_app
from flask_login import login_required
from werkzeug.utils import secure_filename
from arasCore.admin import admin_bp

@admin_bp.route("/settings/uploads/save", methods=["POST"])
@login_required
def settings_upload_save():
    instance_dir = os.path.join(current_app.root_path, "..", "instance")
    cfg_path     = os.path.join(instance_dir, "server.json")
    try:
        with open(cfg_path) as f: cfg = _json.load(f)
    except (FileNotFoundError, ValueError): cfg = {}

    keys = ["UPLOAD_FOLDER", "UPLOAD_IMAGE_FOLDER", "UPLOAD_DOC_FOLDER",
            "UPLOAD_PDF_FOLDER", "UPLOAD_AUDIO_FOLDER"]
    for key in keys:
        val = request.form.get(key, "").strip()
        if val: cfg[key] = val

    os.makedirs(instance_dir, exist_ok=True)
    with open(cfg_path, "w") as f: _json.dump(cfg, f, indent=2)

    flash("Upload paths saved. Restart server to apply.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-uploads")

@admin_bp.route("/settings/server/save", methods=["POST"])
@login_required
def server_settings_save():
    from arasCore.lib.core.server_config import save as save_server_cfg
    data = {
        "wsgi_server":  request.form.get("wsgi_server", "gunicorn"),
        "host":         request.form.get("host", "0.0.0.0"),
        "port":         request.form.get("port", 8080),
        "workers":      request.form.get("workers", 2),
        "threads":      request.form.get("threads", 2),
        "worker_class": request.form.get("worker_class", "sync"),
        "timeout":      request.form.get("timeout", 30),
        "loglevel":     request.form.get("loglevel", "info"),
    }
    save_server_cfg(current_app._get_current_object(), data)
    flash("Server settings saved. Restart to apply.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-server")
