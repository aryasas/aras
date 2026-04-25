# -*- coding: utf-8 -*-
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user

from arasCore.arasAdmin import arasAdmin_bp
from arasCore.arasAdmin.forms import AppManagerAppForm
from arasCore.lib.extensions import db


def _slug_from_url(url: str) -> str:
    return url.strip("/") or "app"


# ── App list ──────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps")
@login_required
def apps():
    from arasCore.arasAdmin.models import AppManagerApp
    all_apps = AppManagerApp.query.order_by(AppManagerApp.id).all()
    return render_template(
        "admin/views/adm_cfg_apps.html",
        title="App Manager",
        main_title="App Manager",
        apps=all_apps,
    )


@arasAdmin_bp.route("/apps/list")
@login_required
def apps_list():
    from arasCore.arasAdmin.models import AppManagerApp
    q = request.args.get("q", "").strip()
    query = AppManagerApp.query.order_by(AppManagerApp.menu_order, AppManagerApp.id)
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(AppManagerApp.url.ilike(like), AppManagerApp.title.ilike(like))
        )
    all_apps = query.all()
    cols = [("Name", "name"), ("Title", "title"), ("URL", "url"), ("Active", "is_active")]
    return render_template(
        "admin/views/adm_list.html",
        title="App Manager",
        main_title="App Manager",
        items=all_apps,
        view_columns=cols,
        edit_url_base="/admin/apps",
        add_url=url_for("admin.apps_new"),
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
        extra_buttons=[
            {"label": "Install App", "url": url_for("admin.apps_install"), "icon": "fa-upload", "style": "outline"},
        ],
    )


@arasAdmin_bp.route("/apps/doctypes")
@login_required
def apps_doctypes():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    q = request.args.get("q", "").strip()
    query = (
        AppManagerTable.query
        .join(AppManagerApp, AppManagerTable.app_id == AppManagerApp.id)
        .order_by(AppManagerApp.url, AppManagerTable.menu_order)
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(AppManagerTable.name.ilike(like), AppManagerTable.db_table_name.ilike(like))
        )
    all_tables = query.all()
    cols = [("Name", "name"), ("DB Table", "db_table_name"), ("Type", "page_type"), ("Active", "is_active")]
    return render_template(
        "admin/views/adm_list.html",
        title="DocTypes",
        main_title="DocTypes",
        items=all_tables,
        view_columns=cols,
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
    )


@arasAdmin_bp.route("/apps/new", methods=["GET", "POST"])
@login_required
def apps_new():
    from arasCore.arasAdmin.models import AppManagerApp
    form = AppManagerAppForm()
    if form.validate_on_submit():
        _slug   = form.url.data.strip().strip("/").lower().replace(" ", "_")
        app_obj = AppManagerApp(
            url=_slug,
            title=form.title.data,
            description=form.description.data or None,
            icon=form.icon.data,
            color_theme=form.color_theme.data or None,
            is_active=form.is_active.data,
            in_sidebar=form.in_sidebar.data,
            require_login=form.require_login.data,
            api_enabled=form.api_enabled.data,
            items_per_page=form.items_per_page.data or 20,
            export_csv=form.export_csv.data,
            export_excel=form.export_excel.data,
            soft_delete=form.soft_delete.data,
            audit_log=form.audit_log.data,
        )
        db.session.add(app_obj)
        db.session.flush()
        current_user.log_activity("app_created", module="app_manager", payload={"app": app_obj.slug})
        db.session.commit()
        flash(f"App '{app_obj.slug}' created.", "success")
        return redirect(url_for("admin.apps"))
    return render_template("admin/views/adm_cfg_app_form.html", title="New App", main_title="New App", form=form)


@arasAdmin_bp.route("/apps/<int:app_id>/", methods=["GET"])
@login_required
def apps_detail(app_id):
    return redirect(url_for("admin.apps_edit", app_id=app_id))


@arasAdmin_bp.route("/apps/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
def apps_edit(app_id):
    from arasCore.arasAdmin.models import AppManagerApp
    app_obj = AppManagerApp.query.get_or_404(app_id)
    form    = AppManagerAppForm(obj=app_obj)
    if form.validate_on_submit():
        _slug = form.url.data.strip().strip("/").lower().replace(" ", "_")
        app_obj.title          = form.title.data
        app_obj.url            = _slug
        app_obj.description    = form.description.data or None
        app_obj.icon           = form.icon.data
        app_obj.color_theme    = form.color_theme.data or None
        app_obj.is_active      = form.is_active.data
        app_obj.in_sidebar     = form.in_sidebar.data
        app_obj.require_login  = form.require_login.data
        app_obj.api_enabled    = form.api_enabled.data
        app_obj.items_per_page = form.items_per_page.data or 20
        app_obj.export_csv     = form.export_csv.data
        app_obj.export_excel   = form.export_excel.data
        app_obj.soft_delete    = form.soft_delete.data
        app_obj.audit_log      = form.audit_log.data
        current_user.log_activity("app_updated", module="app_manager", payload={"app": app_obj.slug})
        db.session.commit()
        try:
            from arasCore.lib.extensions import cache as _cache
            _cache.delete("_sidebar_raw")
        except Exception:
            pass
        if app_obj.is_active:
            from arasCore.arasAdmin.services import _register_built_app, clear_cache
            clear_cache(app_obj.slug)
            ok = _register_built_app(app_obj.id, current_app._get_current_object())
            if ok:
                flash(f"App '{app_obj.slug}' updated and routes re-registered. Restart server if old routes still appear.", "success")
            else:
                flash(f"App '{app_obj.slug}' updated. Route re-registration failed — restart server to apply.", "warning")
        else:
            flash(f"App '{app_obj.slug}' updated.", "success")
        return redirect(url_for("admin.apps"))
    return render_template(
        "admin/views/adm_cfg_app_form.html",
        title=f"Edit — {app_obj.slug}",
        main_title=f"Edit App: {app_obj.slug}",
        form=form,
        app=app_obj,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/activate", methods=["POST"])
@login_required
def apps_activate(app_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = True
    db.session.commit()
    try:
        from arasCore.lib.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    from arasCore.arasAdmin.services import _register_built_app, clear_cache
    clear_cache(app_obj.slug)
    ok = _register_built_app(app_obj.id, current_app._get_current_object())
    try:
        from arasCore.rbac import seed_app_permissions
        resource_slugs = [t.name for t in AppManagerTable.query.filter_by(app_id=app_obj.id, is_active=True).all()]
        if resource_slugs:
            seed_app_permissions(app_obj.slug, resource_slugs, db)
    except Exception as _re:
        current_app.logger.warning(f"[routes] RBAC seed failed on activate for {app_obj.slug}: {_re}")
    if ok:
        flash(f"App '{app_obj.title}' activated and routes registered.", "success")
    else:
        flash(f"App saved as active but route registration failed. Restart server.", "warning")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/deactivate", methods=["POST"])
@login_required
def apps_deactivate(app_id):
    from arasCore.arasAdmin.models import AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = False
    db.session.commit()
    clear_cache(app_obj.slug)
    try:
        from arasCore.lib.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    flash(f"App '{app_obj.title}' deactivated. Restart server for full effect.", "info")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/delete", methods=["POST"])
@login_required
def apps_delete(app_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerField
    from arasCore.arasAdmin.services import clear_cache
    app_obj  = AppManagerApp.query.get_or_404(app_id)
    name     = app_obj.title
    app_slug = app_obj.slug
    clear_cache(app_slug)
    try:
        from arasCore.lib.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    current_user.log_activity("app_deleted", module="app_manager", payload={"app": name})
    AppManagerField.query.filter_by(app_id=app_id).delete()
    db.session.delete(app_obj)
    db.session.commit()
    try:
        from arasCore.rbac import unseed_app_permissions
        unseed_app_permissions(app_slug, db)
    except Exception as _re:
        current_app.logger.warning(f"[routes] RBAC unseed failed for {app_slug}: {_re}")
    flash(f"App '{name}' deleted.", "danger")
    return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/bulk-delete/", methods=["POST"])
@login_required
def apps_bulk_delete():
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerField
    from arasCore.arasAdmin.services import clear_cache
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    deleted = 0
    for app_id in ids:
        app_obj = AppManagerApp.query.get(app_id)
        if not app_obj:
            continue
        clear_cache(app_obj.slug)
        AppManagerField.query.filter_by(app_id=app_id).delete()
        db.session.delete(app_obj)
        deleted += 1
    db.session.commit()
    flash(f"Deleted {deleted} app(s).", "danger")
    return redirect(url_for("admin.settings") + "#panel-apps")


@arasAdmin_bp.route("/apps/tables/bulk-delete/", methods=["POST"])
@login_required
def apps_tables_bulk_delete():
    from arasCore.arasAdmin.models import AppManagerTable
    from arasCore.arasAdmin.services import clear_cache
    ids_raw = request.form.get("ids", "")
    ids = [int(i) for i in ids_raw.split(",") if i.strip().isdigit()]
    deleted = 0
    for table_id in ids:
        tbl = AppManagerTable.query.get(table_id)
        if not tbl:
            continue
        clear_cache(tbl.app.name if tbl.app else "")
        db.session.delete(tbl)
        deleted += 1
    db.session.commit()
    flash(f"Deleted {deleted} doctype(s).", "danger")
    return redirect(url_for("admin.settings") + "#panel-doctypes")


# ── Tables ────────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/tables")
@login_required
def apps_tables(app_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tables  = AppManagerTable.query.filter_by(app_id=app_id).order_by(AppManagerTable.menu_order).all()
    return render_template(
        "admin/views/adm_cfg_tables.html",
        title=f"Tables — {app_obj.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        tables=tables,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/new", methods=["GET", "POST"])
@login_required
def apps_table_new(app_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.forms import AppManagerTableForm
    app_obj = AppManagerApp.query.get_or_404(app_id)
    form    = AppManagerTableForm(app_id=app_id)
    if form.validate_on_submit():
        parent_id = form.parent_table_id.data or None
        tbl = AppManagerTable(
            app_id=app_obj.id,
            parent_table_id=parent_id if parent_id else None,
            name=form.name.data.strip().lower().replace(" ", "_"),
            title=form.title.data,
            url_suffix=form.url_suffix.data.strip(),
            menu_title=form.menu_title.data or None,
            menu_icon=form.menu_icon.data,
            show_in_menu=form.show_in_menu.data,
            menu_order=form.menu_order.data or 0,
            is_active=form.is_active.data,
            search_enabled=form.search_enabled.data,
            sort_field=form.sort_field.data or None,
            sort_direction=form.sort_direction.data,
            list_columns=form.list_columns.data or None,
            display_columns=form.display_columns.data or None,
            per_page=form.per_page.data or 20,
            allow_create=form.allow_create.data,
            allow_edit=form.allow_edit.data,
            allow_delete=form.allow_delete.data,
            detail_view=form.detail_view.data,
        )
        db.session.add(tbl)
        db.session.commit()
        flash(f"Table '{tbl.title}' created. Add columns now.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=tbl.id))
    return render_template(
        "admin/views/adm_cfg_table_form.html",
        title="New Table",
        main_title=app_obj.main_title,
        app_def=app_obj,
        form=form,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/edit", methods=["GET", "POST"])
@login_required
def apps_table_edit(app_id, table_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
    from arasCore.arasAdmin.forms import AppManagerTableForm
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    form    = AppManagerTableForm(app_id=app_id, obj=tbl)
    if form.validate_on_submit():
        tbl.name           = form.name.data.strip().lower().replace(" ", "_")
        tbl.title          = form.title.data
        tbl.url_suffix     = form.url_suffix.data.strip()
        tbl.menu_title     = form.menu_title.data or None
        tbl.menu_icon      = form.menu_icon.data
        tbl.show_in_menu   = form.show_in_menu.data
        tbl.menu_order     = form.menu_order.data or 0
        tbl.is_active      = form.is_active.data
        pid = form.parent_table_id.data
        tbl.parent_table_id = pid if pid else None
        tbl.search_enabled  = form.search_enabled.data
        tbl.sort_field      = form.sort_field.data or None
        tbl.sort_direction  = form.sort_direction.data
        tbl.list_columns    = form.list_columns.data or None
        tbl.display_columns = form.display_columns.data or None
        tbl.per_page        = form.per_page.data or 20
        tbl.allow_create    = form.allow_create.data
        tbl.allow_edit      = form.allow_edit.data
        tbl.allow_delete    = form.allow_delete.data
        tbl.detail_view     = form.detail_view.data
        db.session.commit()
        from arasCore.arasAdmin.services import clear_cache
        from arasCore.lib.label_utils import invalidate_display_cache
        clear_cache(app_obj.slug)
        if tbl.db_table_name:
            invalidate_display_cache(tbl.db_table_name)
        flash(f"Table '{tbl.title}' updated.", "success")
        return redirect(url_for("admin.apps_tables", app_id=app_id))
    return render_template(
        "admin/views/adm_cfg_table_form.html",
        title=f"Edit Table — {tbl.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        form=form,
        tbl=tbl,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/delete", methods=["POST"])
@login_required
def apps_table_delete(app_id, table_id):
    from arasCore.arasAdmin.models import AppManagerTable, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    tbl     = AppManagerTable.query.get_or_404(table_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    title   = tbl.title
    db.session.delete(tbl)
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Table '{title}' deleted.", "danger")
    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── Columns ───────────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns", methods=["GET", "POST"])
@login_required
def apps_columns(app_id, table_id):
    from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable, AppManagerColumn
    from arasCore.arasAdmin.forms import AppManagerColumnForm
    from arasCore.arasAdmin.services import clear_cache, make_table_model, sync_table_columns
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    form    = AppManagerColumnForm(app_id=app_id)
    if form.validate_on_submit():
        rel_tid = form.relation_table_id.data or None
        col = AppManagerColumn(
            table_id=tbl.id,
            name=form.name.data.strip().lower().replace(" ", "_"),
            label=form.label.data,
            field_type=form.field_type.data,
            length=form.length.data or None,
            required=form.required.data,
            default_value=form.default_value.data or None,
            order=form.order.data or 0,
            placeholder=form.placeholder.data or None,
            help_text=form.help_text.data or None,
            show_in_list=form.show_in_list.data,
            show_in_form=form.show_in_form.data,
            readonly=form.readonly.data,
            min_value=form.min_value.data or None,
            max_value=form.max_value.data or None,
            max_length=form.max_length.data or None,
            unique=form.unique.data,
            searchable=form.searchable.data,
            choices=form.choices.data or None,
            relation_table_id=rel_tid if rel_tid else None,
            relation_system_table=form.relation_system_table.data or None,
            relation_display_col=form.relation_display_col.data or None,
            cascade_delete=form.cascade_delete.data,
        )
        db.session.add(col)
        db.session.commit()
        clear_cache(app_obj.slug)
        new_model = make_table_model(tbl, app_obj.slug, AppManagerTable.query.filter_by(app_id=app_id).all())
        sync_table_columns(new_model)
        # Queue schema migration record for audit
        try:
            from arasCore.lib.schema_migrator import diff_app
            diff_app(app_id)
        except Exception:
            pass
        flash(f"Column '{col.label}' added.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))

    columns    = AppManagerColumn.query.filter_by(table_id=table_id).order_by(AppManagerColumn.order).all()
    all_tables = AppManagerTable.query.filter_by(app_id=app_id).all()

    # Pending schema migrations for this table
    pending_migrations = []
    try:
        from arasCore.lib.schema_migrator import get_pending
        pending_migrations = [m for m in get_pending(app_id) if m["table_name"].endswith(tbl.name)]
    except Exception:
        pass

    return render_template(
        "admin/views/adm_cfg_columns.html",
        title=f"Columns — {tbl.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        tbl=tbl,
        columns=columns,
        form=form,
        all_tables=all_tables,
        pending_migrations=pending_migrations,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/delete", methods=["POST"])
@login_required
def apps_column_delete(app_id, table_id, col_id):
    from arasCore.arasAdmin.models import AppManagerColumn, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    col     = AppManagerColumn.query.get_or_404(col_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    label   = col.label
    db.session.delete(col)
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Column '{label}' deleted.", "warning")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


@arasAdmin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/edit", methods=["POST"])
@login_required
def apps_column_edit(app_id, table_id, col_id):
    from arasCore.arasAdmin.models import AppManagerColumn, AppManagerApp
    from arasCore.arasAdmin.services import clear_cache
    col     = AppManagerColumn.query.get_or_404(col_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    col.name          = request.form.get("name", col.name).strip().lower().replace(" ", "_")
    col.label         = request.form.get("label", col.label)
    col.field_type    = request.form.get("field_type", col.field_type)
    col.order         = int(request.form.get("order") or col.order)
    col.required      = request.form.get("required") == "y"
    col.default_value = request.form.get("default_value") or None
    col.placeholder   = request.form.get("placeholder") or None
    col.help_text     = request.form.get("help_text") or None
    col.show_in_list  = request.form.get("show_in_list") == "y"
    col.show_in_form  = request.form.get("show_in_form") == "y"
    col.readonly      = request.form.get("readonly") == "y"
    col.unique        = request.form.get("unique") == "y"
    col.searchable    = request.form.get("searchable") == "y"
    col.choices       = request.form.get("choices") or None
    col.length        = int(request.form.get("length")) if request.form.get("length") else None
    col.max_length    = int(request.form.get("max_length")) if request.form.get("max_length") else None
    col.min_value     = request.form.get("min_value") or None
    col.max_value     = request.form.get("max_value") or None
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Column '{col.label}' updated.", "success")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


# ── Schema migrations (3.4) ───────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/migrations")
@login_required
def apps_migrations(app_id):
    from arasCore.arasAdmin.models import AppManagerApp
    from arasCore.lib.schema_migrator import diff_app, get_pending
    app_obj = AppManagerApp.query.get_or_404(app_id)
    diff_app(app_id)
    pending = get_pending(app_id)
    return render_template(
        "admin/views/adm_cfg_migrations.html",
        title=f"Migrations — {app_obj.title}",
        main_title=app_obj.main_title,
        app_def=app_obj,
        pending=pending,
    )


@arasAdmin_bp.route("/apps/<int:app_id>/migrations/apply", methods=["POST"])
@login_required
def apps_migrations_apply(app_id):
    from arasCore.arasAdmin.models import AppManagerApp
    from arasCore.lib.schema_migrator import apply_pending
    app_obj = AppManagerApp.query.get_or_404(app_id)
    applied, skipped = apply_pending(app_id, safe_only=True)
    flash(
        f"Applied {len(applied)} migration(s). {len(skipped)} skipped (unsafe or error).",
        "success" if applied else "info",
    )
    return redirect(url_for("admin.apps_migrations", app_id=app_id))


@arasAdmin_bp.route("/apps/<int:app_id>/migrations/diff")
@login_required
def apps_migrations_diff(app_id):
    from arasCore.lib.schema_migrator import diff_app, get_pending
    diff_app(app_id)
    return jsonify({"pending": get_pending(app_id)})


# ── Fields (backward compat) ──────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/<int:app_id>/fields")
@login_required
def apps_fields(app_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


@arasAdmin_bp.route("/apps/<int:app_id>/fields/<int:field_id>/delete", methods=["POST"])
@login_required
def apps_field_delete(app_id, field_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── Install / Sync ────────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/install", methods=["GET", "POST"])
@login_required
def apps_install():
    if request.method == "POST":
        install_type = request.form.get("install_type", "definition")

        if install_type == "python":
            f = request.files.get("python_file")
            if not f or not f.filename:
                flash("No zip file selected.", "warning")
                return redirect(url_for("admin.apps_install"))
            if not f.filename.lower().endswith(".zip"):
                flash("Only .zip files accepted for Python install.", "danger")
                return redirect(url_for("admin.apps_install"))
            try:
                from arasCore.lib.middleware import PythonLoaderMiddleware
                result = PythonLoaderMiddleware.from_zip(f, current_app._get_current_object())
                flash(result["message"], "success" if result["registered"] else "info")
                return redirect(url_for("admin.apps"))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                current_app.logger.error(f"Python install error: {e}", exc_info=True)
                flash(f"Install failed: {e}", "danger")
        else:
            f = request.files.get("definition_file")
            if not f or not f.filename:
                flash("No file selected.", "warning")
                return redirect(url_for("admin.apps_install"))
            try:
                from arasCore.lib.installer import load_definition_from_file, install_from_definition
                definition = load_definition_from_file(f)
                app_obj    = install_from_definition(definition, db, current_app._get_current_object())
                flash(f"App '{app_obj.slug}' installed. Add tables/columns and activate when ready.", "success")
                return redirect(url_for("admin.apps_tables", app_id=app_obj.id))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                current_app.logger.error(f"Install error: {e}", exc_info=True)
                flash(f"Install failed: {e}", "danger")

    return render_template("admin/views/adm_cfg_app_install.html", title="Install App", main_title="Install App")


@arasAdmin_bp.route("/apps/install-manifest/<app_name>", methods=["POST"])
@login_required
def apps_install_manifest(app_name):
    import importlib
    from arasCore.lib.installer import sync_helper_to_db
    from arasCore.lib.app_helper import AppHelper

    app_slug = app_name[len("app_"):] if app_name.startswith("app_") else app_name
    pkg_name = f"aras.app_{app_slug}"

    try:
        mod    = importlib.import_module(f"{pkg_name}.manifest")
        helper = getattr(mod, "helper", None)
    except ModuleNotFoundError:
        flash(f"No manifest found for '{pkg_name}'.", "danger")
        return redirect(url_for("admin.apps"))

    if not isinstance(helper, AppHelper):
        flash(f"'{pkg_name}.manifest' has no AppHelper instance.", "danger")
        return redirect(url_for("admin.apps"))

    try:
        app_obj, stats = sync_helper_to_db(helper, db, current_app._get_current_object())
        flash(
            f"Synced '{app_obj.slug}': {stats['tables_new']} new tables, {stats['cols_new']} new columns.",
            "success",
        )
        return redirect(url_for("admin.apps_tables", app_id=app_obj.id))
    except Exception as e:
        current_app.logger.error(f"install-manifest error: {e}", exc_info=True)
        flash(f"Sync failed: {e}", "danger")
        return redirect(url_for("admin.apps"))


@arasAdmin_bp.route("/apps/<int:app_id>/sync", methods=["POST"])
@login_required
def apps_sync(app_id):
    import importlib
    from arasCore.lib.installer import sync_helper_to_db
    from arasCore.lib.app_helper import AppHelper
    from arasCore.arasAdmin.models import AppManagerApp

    app_obj = AppManagerApp.query.get_or_404(app_id)
    from arasCore.lib.blueprints import get_helper_registry
    helper = get_helper_registry().get(app_obj.slug)

    if helper is None:
        pkg_name = f"aras.app_{app_obj.slug}"
        try:
            mod    = importlib.import_module(f"{pkg_name}.manifest")
            helper = getattr(mod, "helper", None)
        except ModuleNotFoundError:
            flash(f"No Python manifest found for '{app_obj.slug}'.", "warning")
            return redirect(url_for("admin.apps_tables", app_id=app_id))

    if not isinstance(helper, AppHelper):
        flash("App has no AppHelper manifest — nothing to sync.", "warning")
        return redirect(url_for("admin.apps_tables", app_id=app_id))

    try:
        _, stats = sync_helper_to_db(helper, db, current_app._get_current_object())
        flash(
            f"Sync complete: {stats['tables_new']} new tables, {stats['cols_new']} new columns "
            f"({stats['cols_skipped']} already existed).",
            "success",
        )
    except Exception as e:
        current_app.logger.error(f"sync error: {e}", exc_info=True)
        flash(f"Sync failed: {e}", "danger")

    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── Templates & Export ────────────────────────────────────────────────────────

@arasAdmin_bp.route("/apps/template/yaml")
@login_required
def apps_template_yaml():
    from flask import Response
    from arasCore.lib.installer import generate_yaml_template
    content = generate_yaml_template()
    return Response(content, mimetype="text/yaml",
                    headers={"Content-Disposition": "attachment;filename=aras_app_template.yaml"})


@arasAdmin_bp.route("/apps/template/json")
@login_required
def apps_template_json():
    from flask import Response
    from arasCore.lib.installer import generate_json_template
    content = generate_json_template()
    return Response(content, mimetype="application/json",
                    headers={"Content-Disposition": "attachment;filename=aras_app_template.json"})


@arasAdmin_bp.route("/apps/<int:app_id>/export/yaml")
@login_required
def apps_export_yaml(app_id):
    import yaml
    from flask import Response
    from arasCore.arasAdmin.models import AppManagerApp
    app_obj    = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content    = yaml.dump(definition, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return Response(content.encode("utf-8"), mimetype="text/yaml",
                    headers={"Content-Disposition": f"attachment;filename={app_obj.slug}.yaml"})


@arasAdmin_bp.route("/apps/<int:app_id>/export/json")
@login_required
def apps_export_json(app_id):
    import json
    from flask import Response
    from arasCore.arasAdmin.models import AppManagerApp
    app_obj    = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content    = json.dumps(definition, indent=2, ensure_ascii=False)
    return Response(content.encode("utf-8"), mimetype="application/json",
                    headers={"Content-Disposition": f"attachment;filename={app_obj.slug}.json"})


def _build_export_definition(app_obj) -> dict:
    from arasCore.arasAdmin.models import AppManagerTable, AppManagerColumn
    tables     = AppManagerTable.query.filter_by(app_id=app_obj.id).order_by(AppManagerTable.menu_order).all()
    tables_out = []
    for tbl in tables:
        cols = AppManagerColumn.query.filter_by(table_id=tbl.id).order_by(AppManagerColumn.order).all()
        tables_out.append({
            "name":           tbl.name,
            "title":          tbl.title,
            "url_suffix":     tbl.url_suffix,
            "menu_title":     tbl.menu_title or tbl.title,
            "menu_icon":      tbl.menu_icon,
            "show_in_menu":   tbl.show_in_menu,
            "menu_order":     tbl.menu_order,
            "is_active":      tbl.is_active,
            "allow_create":   tbl.allow_create,
            "allow_edit":     tbl.allow_edit,
            "allow_delete":   tbl.allow_delete,
            "detail_view":    tbl.detail_view,
            "search_enabled": tbl.search_enabled,
            "sort_field":     tbl.sort_field,
            "sort_direction": tbl.sort_direction,
            "columns": [
                {
                    "name":          c.name,
                    "label":         c.label,
                    "field_type":    c.field_type,
                    "required":      c.required,
                    "order":         c.order,
                    "show_in_list":  c.show_in_list,
                    "show_in_form":  c.show_in_form,
                    "readonly":      c.readonly,
                    "unique":        c.unique,
                    "searchable":    c.searchable,
                    "placeholder":   c.placeholder,
                    "help_text":     c.help_text,
                    "default_value": c.default_value,
                    "max_length":    c.max_length,
                    "choices":       c.choices,
                    "relation_system_table": c.relation_system_table,
                    "relation_display_col":  c.relation_display_col,
                }
                for c in cols
            ],
        })
    return {
        "app": {
            "url":            app_obj.url,
            "title":          app_obj.title,
            "description":    app_obj.description,
            "icon":           app_obj.icon,
            "is_active":      app_obj.is_active,
            "in_sidebar":     app_obj.in_sidebar,
            "require_login":  app_obj.require_login,
            "api_enabled":    app_obj.api_enabled,
            "items_per_page": app_obj.items_per_page,
            "export_csv":     app_obj.export_csv,
            "export_excel":   app_obj.export_excel,
            "soft_delete":    app_obj.soft_delete,
            "audit_log":      app_obj.audit_log,
            "menu_order":     app_obj.menu_order,
        },
        "tables": tables_out,
    }
