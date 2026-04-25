# -*- coding: utf-8 -*-
from flask import render_template
from flask_login import login_required

from arasCore.arasAdmin import arasAdmin_bp


@arasAdmin_bp.route("/dev")
@login_required
def dev():
    from flask import current_app
    import sys as _sys
    routes = []
    for rule in sorted(current_app.url_map.iter_rules(), key=lambda r: r.rule):
        routes.append({
            "rule":     rule.rule,
            "endpoint": rule.endpoint,
            "methods":  ", ".join(sorted(m for m in rule.methods if m not in ("HEAD", "OPTIONS"))),
        })
    modules = sorted(k for k in _sys.modules if k.startswith("arasCore") or k.startswith("aras."))
    return render_template(
        "admin/views/adm_dev.html",
        main_title="Dev Page",
        routes=routes,
        modules=modules,
    )
