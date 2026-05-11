# -*- coding: utf-8 -*-
from flask import request, redirect, url_for, flash, render_template
from flask_login import login_required
from arasCore.admin import admin_bp
from arasCore.lib.core.extensions import db

@admin_bp.route("/settings/db/<table_name>/")
@login_required
def db_table_detail(table_name):
    from sqlalchemy import inspect as sa_inspect
    inspector = sa_inspect(db.engine)
    if table_name not in inspector.get_table_names():
        from flask import abort
        abort(404)
    columns = inspector.get_columns(table_name)
    pk_cols = {c for c in inspector.get_pk_constraint(table_name).get("constrained_columns", [])}
    indexes = inspector.get_indexes(table_name)
    return render_template(
        "admin/setting/setting_db_detail.html",
        title=table_name, main_title=table_name,
        table_name=table_name, columns=columns,
        pk_cols=pk_cols, indexes=indexes,
    )

@admin_bp.route("/settings/db/generate-view", methods=["POST"])
@login_required
def db_generate_view():
    from arasCore.admin.models import AppManagerApp
    table_name = request.form.get("table_name", "").strip()
    if not table_name:
        flash("No table selected.", "warning")
        return redirect(url_for("admin.settings") + "?panel=panel-database")

    existing = AppManagerApp.query.filter_by(url=table_name).first()
    if existing:
        flash(f"App for table '{table_name}' already exists.", "info")
        return redirect(url_for("admin.settings") + "?panel=panel-database")

    slug   = table_name.replace("-", "_")
    title  = slug.replace("_", " ").title()
    app_obj = AppManagerApp(url=slug, title=title, is_active=False, in_sidebar=True)
    db.session.add(app_obj)
    db.session.commit()
    flash(f"App '{title}' created from table '{table_name}'. Activate it in App Manager.", "success")
    return redirect(url_for("admin.settings") + "?panel=panel-apps")
