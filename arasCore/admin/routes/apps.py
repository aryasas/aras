# -*- coding: utf-8 -*-
from flask import render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user

from arasCore.admin import admin_bp
from arasCore.admin.forms import AppManagerAppForm
from arasCore.lib.core.extensions import db


def _slug_from_url(url: str) -> str:
    return url.strip("/") or "app"


# ── App list ──────────────────────────────────────────────────────────────────

@admin_bp.route("/apps")
@login_required
def apps():
    from arasCore.admin.models import AppManagerApp
    all_apps = AppManagerApp.query.order_by(AppManagerApp.id).all()
    return render_template(
        "admin/setting/setting_apps.html",
        title="App Manager",
        main_title="App Manager",
        apps=all_apps,
    )


@admin_bp.route("/apps/list")
@login_required
def apps_list():
    from arasCore.admin.models import AppManagerApp
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
        "admin/gen/gen_view_list.html",
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


@admin_bp.route("/apps/doctypes")
@login_required
def apps_doctypes():
    from arasCore.admin.models import AppManagerApp, AppManagerTable
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
        "admin/gen/gen_view_list.html",
        title="DocTypes",
        main_title="DocTypes",
        items=all_tables,
        view_columns=cols,
        search_enabled=True,
        search_q=q,
        filter_cols=cols,
        active_filters=[],
    )


@admin_bp.route("/api/render-child-row/<string:model_name>/<int:item_id>")
@login_required
def render_child_row(model_name, item_id):
    from arasCore.admin.crud_factory import _get_child_tables_for_model
    from arasCore.lib.services.api_handler import get_api_registry
    
    parent_model_name = request.args.get("parent_model")
    li = request.args.get("li", "0")
    
    # 1. Find child model
    registry = get_api_registry()
    child_entry = None
    for entry in registry.values():
        if entry["model"].__tablename__ == model_name:
            child_entry = entry
            break
            
    if not child_entry:
        return f"Child model {model_name} not found", 404
        
    child_model = child_entry["model"]
    obj = child_model.query.get_or_404(item_id)
    
    # 2. Find parent model and its child table config
    parent_model = None
    if parent_model_name:
        for entry in registry.values():
            if entry["model"].__tablename__ == parent_model_name:
                parent_model = entry["model"]
                break
    
    if not parent_model:
        return f"Parent model {parent_model_name} not found", 404
        
    cts = _get_child_tables_for_model(parent_model)
    ct = None
    for c in cts:
        if c["model_name"] == model_name:
            ct = c
            break
            
    if not ct:
        return f"Child table config for {model_name} not found in {parent_model_name}", 404
        
    # 3. Render the row
    from arasCore.admin.crud_factory import _smart_vcols
    _ct_vcol_names = ct["vcols"] | map(attribute=1) | list if isinstance(ct["vcols"], list) else []
    # Actually _get_child_tables_for_model already did a lot of work.
    # Let's just use what's in ct.
    
    # Re-calculate some helper vars needed by the template
    _ct_all_render = ct["all_columns"]
    _ct_vcol_names = [v[1] for v in ct["vcols"]]
    
    return render_template(
        "admin/gen/_child_table_row.html",
        row=obj,
        ct=ct,
        _li=li,
        _ct_all_render=_ct_all_render,
        _ct_vcol_names=_ct_vcol_names
    )


@admin_bp.route("/api/child-table/<string:model_name>/save", methods=["POST"])
@login_required
def child_table_save(model_name):
    from arasCore.lib.services.api_handler import get_api_registry
    from arasCore.admin.crud_factory import _get_child_tables_for_model
    
    parent_model_name = request.args.get("parent_model")
    li = request.args.get("li", "0")
    item_id = request.args.get("id")
    fk_col_param = request.args.get("fk_col", "").strip()
    parent_id_param = request.args.get("parent_id", "").strip()
    
    # 1. Find child model
    registry = get_api_registry()
    child_entry = None
    for entry in registry.values():
        if entry["model"].__tablename__ == model_name:
            child_entry = entry
            break
            
    if not child_entry:
        return jsonify({"error": f"Child model {model_name} not found"}), 404
        
    child_model = child_entry["model"]
    
    # 2. Create or Update the record
    raw_data = request.get_json(silent=True)
    if raw_data is None:
        raw_data = request.form.to_dict()
    if not raw_data:
        raw_data = {}
    data = {}
    for k, v in raw_data.items():
        if v in ("", "None", "null", "__PID__", None):
            # If the column is nullable, we can set it to None.
            # If it's NOT nullable, we skip it to allow model defaults to take over (if new)
            # or to avoid setting an invalid empty string.
            col = child_model.__table__.columns.get(k)
            if col is not None and col.nullable:
                data[k] = None
            continue
        data[k] = v

    # Inject parent FK from URL params if body sent "None"/empty for it
    if fk_col_param and parent_id_param and parent_id_param not in ("None", "null", "", "__PID__"):
        if not data.get(fk_col_param):
            data[fk_col_param] = parent_id_param

    # Auto-fill invoice_type for polymorphic FK tables (e.g. acc_payment_allocation)
    if "invoice_type" in child_model.__table__.columns and not data.get("invoice_type"):
        if parent_model_name and "sales" in parent_model_name:
            data["invoice_type"] = "sales"
        elif parent_model_name and "purchase" in parent_model_name:
            data["invoice_type"] = "purchase"

    try:
        user_id = getattr(current_user, "id", None)
        if item_id and not item_id.startswith("local_"):
            obj = child_model.query.get_or_404(item_id)
            obj.update_self(data, user_id=user_id)
        else:
            # Auto-fill description if missing and product_id is present
            if not data.get("description") and data.get("product_id"):
                try:
                    from aras.erp.erp_stock.models.product import StockProduct
                    p = StockProduct.query.get(data["product_id"])
                    if p:
                        data["description"] = p.name
                except Exception:
                    pass
            obj = child_model.create(data, user_id=user_id)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        import logging
        logging.getLogger(__name__).error(f"Error in child_table_save for {model_name}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
        
    # 3. Find parent model and its child table config for rendering
    parent_model = None
    if parent_model_name:
        for entry in registry.values():
            if entry["model"].__tablename__ == parent_model_name:
                parent_model = entry["model"]
                break
    
    if not parent_model:
        return f"Parent model {parent_model_name} not found", 404
        
    cts = _get_child_tables_for_model(parent_model)
    ct = None
    for c in cts:
        if c["model_name"] == model_name:
            ct = c
            break
            
    if not ct:
        return f"Child table config for {model_name} not found in {parent_model_name}", 404
        
    # Re-calculate helper vars
    _ct_all_render = ct["all_columns"]
    _ct_vcol_names = [v[1] for v in ct["vcols"]]
    
    return render_template(
        "admin/gen/_child_table_row.html",
        row=obj,
        ct=ct,
        _li=li,
        _ct_all_render=_ct_all_render,
        _ct_vcol_names=_ct_vcol_names
    )


@admin_bp.route("/apps/wizard", methods=["GET", "POST"])
@login_required
def apps_wizard():
    if request.method == "POST":
        data = request.get_json() or {}
        
        # Step 1: Create App
        app_data = data.get("app", {})
        if not app_data.get("title") or not app_data.get("url"):
            return jsonify({"ok": False, "error": "App title and URL are required"}), 400
            
        from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn
        
        try:
            _slug = app_data["url"].strip().strip("/").lower().replace(" ", "_")
            app_obj = AppManagerApp(
                url=_slug,
                title=app_data["title"],
                description=app_data.get("description"),
                icon=app_data.get("icon", "fa-cubes"),
                color_theme=app_data.get("color_theme"),
                is_active=True,
                in_sidebar=True,
                require_login=True,
                api_enabled=True,
                items_per_page=20,
            )
            db.session.add(app_obj)
            db.session.flush() # Get app_obj.id
            
            # Step 2: Create Tables
            tables_data = data.get("tables", [])
            for t_data in tables_data:
                tbl = AppManagerTable(
                    app_id=app_obj.id,
                    name=t_data["name"].strip().lower().replace(" ", "_"),
                    title=t_data["title"],
                    url_suffix=f"/{t_data['name'].strip().lower()}",
                    is_active=True,
                    show_in_menu=True,
                    allow_create=True,
                    allow_edit=True,
                    allow_delete=True
                )
                db.session.add(tbl)
                db.session.flush() # Get tbl.id
                
                # Step 3: Create Columns for this table
                cols_data = t_data.get("columns", [])
                for i, c_data in enumerate(cols_data):
                    col = AppManagerColumn(
                        table_id=tbl.id,
                        name=c_data["name"].strip().lower().replace(" ", "_"),
                        label=c_data["label"],
                        field_type=c_data.get("field_type", "string"),
                        required=bool(c_data.get("required")),
                        order=i,
                        show_in_list=True,
                        show_in_form=True
                    )
                    db.session.add(col)
            
            db.session.commit()
            flash(f"App '{app_obj.title}' created successfully via wizard.", "success")
            return jsonify({"ok": True, "redirect": url_for("admin.apps_tables", app_id=app_obj.id)})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"ok": False, "error": str(e)}), 500
            
    return render_template("admin/setting/setting_app_wizard.html", title="App Wizard", main_title="App Wizard")


@admin_bp.route("/apps/new", methods=["GET", "POST"])
@login_required
def apps_new():
    from arasCore.admin.models import AppManagerApp
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
    return render_template("admin/setting/setting_app_form.html", title="New App", main_title="New App", form=form)


@admin_bp.route("/apps/<int:app_id>/", methods=["GET"])
@login_required
def apps_detail(app_id):
    return redirect(url_for("admin.apps_edit", app_id=app_id))


@admin_bp.route("/apps/<int:app_id>/edit", methods=["GET", "POST"])
@login_required
def apps_edit(app_id):
    from arasCore.admin.models import AppManagerApp
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
            from arasCore.lib.core.extensions import cache as _cache
            _cache.delete("_sidebar_raw")
        except Exception:
            pass
        if app_obj.is_active:
            from arasCore.admin.services import _register_built_app, clear_cache
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
        "admin/setting/setting_app_form.html",
        title=f"Edit — {app_obj.slug}",
        main_title=f"Edit App: {app_obj.slug}",
        form=form,
        app=app_obj,
    )


@admin_bp.route("/apps/<int:app_id>/activate", methods=["POST"])
@login_required
def apps_activate(app_id):
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = True
    db.session.commit()
    try:
        from arasCore.lib.core.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    from arasCore.admin.services import _register_built_app, clear_cache
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


@admin_bp.route("/apps/<int:app_id>/deactivate", methods=["POST"])
@login_required
def apps_deactivate(app_id):
    from arasCore.admin.models import AppManagerApp
    from arasCore.admin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    app_obj.is_active = False
    db.session.commit()
    clear_cache(app_obj.slug)
    try:
        from arasCore.lib.core.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    flash(f"App '{app_obj.title}' deactivated. Restart server for full effect.", "info")
    return redirect(url_for("admin.apps"))


@admin_bp.route("/apps/<int:app_id>/delete", methods=["POST"])
@login_required
def apps_delete(app_id):
    from arasCore.admin.models import AppManagerApp, AppManagerField
    from arasCore.admin.services import clear_cache
    app_obj  = AppManagerApp.query.get_or_404(app_id)
    name     = app_obj.title
    app_slug = app_obj.slug
    clear_cache(app_slug)
    try:
        from arasCore.lib.core.extensions import cache as _cache
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


@admin_bp.route("/apps/bulk-delete/", methods=["POST"])
@login_required
def apps_bulk_delete():
    from arasCore.admin.models import AppManagerApp, AppManagerField
    from arasCore.admin.services import clear_cache
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


@admin_bp.route("/apps/tables/bulk-delete/", methods=["POST"])
@login_required
def apps_tables_bulk_delete():
    from arasCore.admin.models import AppManagerTable
    from arasCore.admin.services import clear_cache
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

@admin_bp.route("/apps/<int:app_id>/tables")
@login_required
def apps_tables(app_id):
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tables  = AppManagerTable.query.filter_by(app_id=app_id).order_by(AppManagerTable.menu_order).all()
    return render_template(
        "admin/setting/setting_tables.html",
        title=f"Tables — {app_obj.title}",
        main_title=app_obj.title,
        app_def=app_obj,
        tables=tables,
    )


@admin_bp.route("/apps/<int:app_id>/tables/new", methods=["GET", "POST"])
@login_required
def apps_table_new(app_id):
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    from arasCore.admin.forms import AppManagerTableForm
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
        "admin/setting/setting_table_form.html",
        title="New Table",
        main_title=app_obj.title,
        app_def=app_obj,
        form=form,
    )


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/edit", methods=["GET", "POST"])
@login_required
def apps_table_edit(app_id, table_id):
    from arasCore.admin.models import AppManagerApp, AppManagerTable
    from arasCore.admin.forms import AppManagerTableForm
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
        from arasCore.admin.services import clear_cache
        from arasCore.lib.ui.label_utils import invalidate_display_cache
        clear_cache(app_obj.slug)
        if tbl.db_table_name:
            invalidate_display_cache(tbl.db_table_name)
        flash(f"Table '{tbl.title}' updated.", "success")
        return redirect(url_for("admin.apps_tables", app_id=app_id))
    return render_template(
        "admin/setting/setting_table_form.html",
        title=f"Edit Table — {tbl.title}",
        main_title=app_obj.title,
        app_def=app_obj,
        form=form,
        tbl=tbl,
    )


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/delete", methods=["POST"])
@login_required
def apps_table_delete(app_id, table_id):
    from arasCore.admin.models import AppManagerTable, AppManagerApp
    from arasCore.admin.services import clear_cache
    tbl     = AppManagerTable.query.get_or_404(table_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    title   = tbl.title
    db.session.delete(tbl)
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Table '{title}' deleted.", "danger")
    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── Columns ───────────────────────────────────────────────────────────────────

@admin_bp.route("/api/fk-choices/", methods=["GET"])
@login_required
def api_fk_choices():
    """Return [{id, label}] for a given relation_table_id or system table name."""
    from flask import request, jsonify
    from arasCore.admin.models import AppManagerTable, AppManagerColumn
    table_id = request.args.get("table_id", type=int)
    system_table = request.args.get("system_table", "").strip()
    display_col = request.args.get("display_col", "").strip()

    rows = []
    try:
        if table_id:
            tbl = AppManagerTable.query.get(table_id)
            if tbl:
                from arasCore.admin.services import make_table_model
                model = make_table_model(tbl, tbl.app.slug if tbl.app else "app",
                                         AppManagerTable.query.filter_by(app_id=tbl.app_id).all())
                label_col = display_col or (tbl.columns[0].name if tbl.columns else "id")
                for obj in model.query.order_by(model.id).limit(200).all():
                    rows.append({"id": obj.id, "label": str(getattr(obj, label_col, obj.id) or obj.id)})
        elif system_table:
            from sqlalchemy import text
            from arasCore.lib.core.extensions import db
            label_col = display_col or "name"
            try:
                result = db.session.execute(
                    text(f"SELECT id, {label_col} FROM {system_table} ORDER BY id LIMIT 200")
                )
                for row in result:
                    rows.append({"id": row[0], "label": str(row[1] or row[0])})
            except Exception:
                result = db.session.execute(text(f"SELECT id FROM {system_table} ORDER BY id LIMIT 200"))
                rows = [{"id": row[0], "label": str(row[0])} for row in result]
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

    return jsonify({"ok": True, "rows": rows})


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns", methods=["GET", "POST"])
@login_required
def apps_columns(app_id, table_id):
    from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn
    from arasCore.admin.forms import AppManagerColumnForm
    from arasCore.admin.services import clear_cache, make_table_model, sync_table_columns
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
            default_section=form.default_section.data or 'content',
        )
        db.session.add(col)
        db.session.commit()
        clear_cache(app_obj.slug)
        new_model = make_table_model(tbl, app_obj.slug, AppManagerTable.query.filter_by(app_id=app_id).all())
        sync_table_columns(new_model)
        # Queue schema migration record for audit
        try:
            from arasCore.lib.services.schema_migrator import diff_app
            diff_app(app_id)
        except Exception:
            pass
        flash(f"Column '{col.label}' added.", "success")
        return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))

    columns    = AppManagerColumn.query.filter_by(table_id=table_id).order_by(AppManagerColumn.order).all()
    all_tables_in_app = AppManagerTable.query.filter_by(app_id=app_id).all()

    # ── Find Child Tables to pass to Form Designer ──
    child_table_defs = []
    seen_child_names = set()

    # 1. Dynamic tables: find FK columns pointing to this table
    for potential_child in all_tables_in_app:
        if potential_child.id == table_id:
            continue
        fk_cols = [c for c in potential_child.columns if c.field_type == 'relation' and c.relation_table_id == table_id]
        if fk_cols:
            child_table_defs.append({
                "name": potential_child.name, 
                "label": potential_child.title, 
                "type": "child_table",
                "app_id": potential_child.app_id,
                "table_id": potential_child.id
            })
            seen_child_names.add(potential_child.name)

    # 2. Code-based models: detect via SQLAlchemy relationships on the live model
    try:
        from arasCore.admin.crud_factory import _get_child_tables_for_model
        from arasCore.lib.services.api_handler import get_api_registry
        tbl_name_norm = tbl.name.replace("/", "_").replace("-", "_")
        registry = get_api_registry()
        model_cls = next((v["model"] for v in registry.values()
                          if getattr(v.get("model"), "__tablename__", None) == tbl_name_norm), None)
        if model_cls:
            for cd in _get_child_tables_for_model(model_cls):
                cname = cd.get("model_name") or cd["model"].__tablename__
                if cname not in seen_child_names:
                    child_table_defs.append({
                        "name": cname, 
                        "label": cd.get("title", cname), 
                        "type": "child_table",
                        "app_id": cd.get("app_id"),
                        "table_id": cd.get("table_id")
                    })
                    seen_child_names.add(cname)
    except Exception:
        pass

    # Pending schema migrations for this table
    pending_migrations = []
    try:
        from arasCore.lib.services.schema_migrator import get_pending
        pending_migrations = [m for m in get_pending(app_id) if m["table_name"].endswith(tbl.name)]
    except Exception:
        pass

    return render_template(
        "admin/setting/setting_columns.html",
        title=f"Columns — {tbl.title}",
        main_title=app_obj.title,
        app_def=app_obj,
        tbl=tbl,
        columns=columns,
        child_tables=child_table_defs,  # Pass to template
        form=form,
        all_tables=all_tables_in_app,
        pending_migrations=pending_migrations,
    )


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/delete", methods=["POST"])
@login_required
def apps_column_delete(app_id, table_id, col_id):
    from arasCore.admin.models import AppManagerColumn, AppManagerApp, AppManagerTable
    from arasCore.admin.services import clear_cache
    col     = AppManagerColumn.query.get_or_404(col_id)
    app_obj = AppManagerApp.query.get_or_404(app_id)
    label   = col.label
    tbl     = AppManagerTable.query.get(table_id)
    db.session.delete(col)
    if tbl:
        tbl.layout_json = None  # force regeneration without deleted column
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Column '{label}' deleted.", "warning")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/columns/<int:col_id>/edit", methods=["POST"])
@login_required
def apps_column_edit(app_id, table_id, col_id):
    from arasCore.admin.models import AppManagerColumn, AppManagerApp
    from arasCore.admin.services import clear_cache
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
    _ds = request.form.get("default_section", "content")
    col.default_section = _ds if _ds in ('header', 'content', 'extra', 'footer') else 'content'
    db.session.commit()
    clear_cache(app_obj.slug)
    flash(f"Column '{col.label}' updated.", "success")
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id))


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/form-builder")
@login_required
def apps_table_form_builder(app_id, table_id):
    """Redirect to the merged designer tab in apps_columns."""
    return redirect(url_for("admin.apps_columns", app_id=app_id, table_id=table_id) + "#designer-pane")


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/layout", methods=["POST"])
@login_required
def apps_table_layout_save(app_id, table_id):
    """Save layout_json for a table (from the form builder)."""
    import json
    from arasCore.admin.models import AppManagerTable, AppManagerApp
    from arasCore.admin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    data    = request.get_json(silent=True) or {}
    layout  = data.get("layout")
    if layout is None:
        return {"ok": False, "error": "No layout provided"}, 400
    
    tbl.layout_json = json.dumps(layout) if not isinstance(layout, str) else layout
    db.session.add(tbl)
    db.session.commit()
    clear_cache(app_obj.slug)
    return {"ok": True}


@admin_bp.route("/apps/<int:app_id>/tables/<int:table_id>/layout/reset", methods=["POST"])
@login_required
def apps_table_layout_reset(app_id, table_id):
    """Clear layout_json so the next form open regenerates and saves a fresh default."""
    from arasCore.admin.models import AppManagerTable, AppManagerApp
    from arasCore.admin.services import clear_cache
    app_obj = AppManagerApp.query.get_or_404(app_id)
    tbl     = AppManagerTable.query.get_or_404(table_id)
    tbl.layout_json = None
    db.session.commit()
    clear_cache(app_obj.slug)
    return {"ok": True}


# ── Schema migrations (3.4) ───────────────────────────────────────────────────

@admin_bp.route("/apps/<int:app_id>/migrations")
@login_required
def apps_migrations(app_id):
    from arasCore.admin.models import AppManagerApp
    from arasCore.lib.services.schema_migrator import diff_app, get_pending, get_history
    app_obj = AppManagerApp.query.get_or_404(app_id)
    diff_app(app_id)
    pending = get_pending(app_id)
    history = get_history(app_id)
    return render_template(
        "admin/setting/setting_migrations.html",
        title=f"Migrations — {app_obj.title}",
        main_title=app_obj.title,
        app_def=app_obj,
        pending=pending,
        history=history,
    )


@admin_bp.route("/apps/<int:app_id>/migrations/apply", methods=["POST"])
@login_required
def apps_migrations_apply(app_id):
    from arasCore.admin.models import AppManagerApp
    from arasCore.lib.services.schema_migrator import apply_pending
    app_obj = AppManagerApp.query.get_or_404(app_id)
    applied, skipped = apply_pending(app_id, safe_only=True)
    flash(
        f"Applied {len(applied)} safe migration(s). {len(skipped)} skipped (unsafe or error).",
        "success" if applied else "info",
    )
    return redirect(url_for("admin.apps_migrations", app_id=app_id))


@admin_bp.route("/apps/<int:app_id>/migrations/apply-all", methods=["POST"])
@login_required
def apps_migrations_apply_all(app_id):
    from arasCore.admin.models import AppManagerApp
    from arasCore.lib.services.schema_migrator import apply_pending
    app_obj = AppManagerApp.query.get_or_404(app_id)
    applied, skipped = apply_pending(app_id, safe_only=False)
    if skipped:
        flash(f"Applied {len(applied)} migration(s), but {len(skipped)} failed.", "warning")
    else:
        flash(f"Successfully applied all {len(applied)} migration(s).", "success")
    return redirect(url_for("admin.apps_migrations", app_id=app_id))


@admin_bp.route("/apps/<int:app_id>/migrations/diff")
@login_required
def apps_migrations_diff(app_id):
    from arasCore.lib.services.schema_migrator import diff_app, get_pending
    diff_app(app_id)
    return jsonify({"pending": get_pending(app_id)})


# ── Fields (backward compat) ──────────────────────────────────────────────────

@admin_bp.route("/apps/<int:app_id>/fields")
@login_required
def apps_fields(app_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


@admin_bp.route("/apps/<int:app_id>/fields/<int:field_id>/delete", methods=["POST"])
@login_required
def apps_field_delete(app_id, field_id):
    return redirect(url_for("admin.apps_tables", app_id=app_id))


# ── Install / Sync ────────────────────────────────────────────────────────────

@admin_bp.route("/apps/install", methods=["GET", "POST"])
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
                from arasCore.lib.services.installer import load_definition_from_file, install_from_definition
                definition = load_definition_from_file(f)
                app_obj    = install_from_definition(definition, db, current_app._get_current_object())
                flash(f"App '{app_obj.slug}' installed. Add tables/columns and activate when ready.", "success")
                return redirect(url_for("admin.apps_tables", app_id=app_obj.id))
            except ValueError as e:
                flash(str(e), "danger")
            except Exception as e:
                current_app.logger.error(f"Install error: {e}", exc_info=True)
                flash(f"Install failed: {e}", "danger")

    return render_template("admin/setting/setting_app_install.html", title="Install App", main_title="Install App")


@admin_bp.route("/apps/install-manifest/<app_name>", methods=["POST"])
@login_required
def apps_install_manifest(app_name):
    import importlib
    from arasCore.lib.services.installer import sync_helper_to_db
    from arasCore.lib.services.app_helper import AppHelper

    app_slug = app_name[len("app_"):] if app_name.startswith("app_") else app_name
    pkg_name = f"aras.{app_slug}"

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


@admin_bp.route("/apps/<int:app_id>/sync", methods=["POST"])
@login_required
def apps_sync(app_id):
    import importlib
    from arasCore.lib.services.installer import sync_helper_to_db
    from arasCore.lib.services.app_helper import AppHelper
    from arasCore.admin.models import AppManagerApp

    app_obj = AppManagerApp.query.get_or_404(app_id)
    from arasCore.lib.services.blueprints import get_helper_registry
    helper = get_helper_registry().get(app_obj.slug)

    if helper is None:
        pkg_name = f"aras.{app_obj.slug}"
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

@admin_bp.route("/apps/template/yaml")
@login_required
def apps_template_yaml():
    from flask import Response
    from arasCore.lib.services.installer import generate_yaml_template
    content = generate_yaml_template()
    return Response(content, mimetype="text/yaml",
                    headers={"Content-Disposition": "attachment;filename=aras_app_template.yaml"})


@admin_bp.route("/apps/template/json")
@login_required
def apps_template_json():
    from flask import Response
    from arasCore.lib.services.installer import generate_json_template
    content = generate_json_template()
    return Response(content, mimetype="application/json",
                    headers={"Content-Disposition": "attachment;filename=aras_app_template.json"})


@admin_bp.route("/apps/<int:app_id>/export/yaml")
@login_required
def apps_export_yaml(app_id):
    import yaml
    from flask import Response
    from arasCore.admin.models import AppManagerApp
    app_obj    = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content    = yaml.dump(definition, allow_unicode=True, default_flow_style=False, sort_keys=False)
    return Response(content.encode("utf-8"), mimetype="text/yaml",
                    headers={"Content-Disposition": f"attachment;filename={app_obj.slug}.yaml"})


@admin_bp.route("/apps/<int:app_id>/export/json")
@login_required
def apps_export_json(app_id):
    import json
    from flask import Response
    from arasCore.admin.models import AppManagerApp
    app_obj    = AppManagerApp.query.get_or_404(app_id)
    definition = _build_export_definition(app_obj)
    content    = json.dumps(definition, indent=2, ensure_ascii=False)
    return Response(content.encode("utf-8"), mimetype="application/json",
                    headers={"Content-Disposition": f"attachment;filename={app_obj.slug}.json"})


def _build_export_definition(app_obj) -> dict:
    from arasCore.admin.models import AppManagerTable, AppManagerColumn
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


# ── List view preferences ─────────────────────────────────────────────────────

@admin_bp.route("/api/list-pref/", methods=["POST"])
@login_required
def list_pref_save():
    """Saves per-user column visibility for a given doctype."""
    import json
    from arasCore.admin.models import ListViewSetting
    data = request.get_json() or {}
    doctype = data.get("doctype")
    columns = data.get("columns")

    if not doctype or columns is None:
        return jsonify({"ok": False, "error": "Missing doctype or columns"}), 400

    try:
        s = ListViewSetting.query.filter_by(user_id=current_user.id, doctype=doctype).first()
        if not s:
            s = ListViewSetting(user_id=current_user.id, doctype=doctype)
            db.session.add(s)

        s.columns_json = json.dumps(columns)
        db.session.commit()
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@admin_bp.route("/api/page-view/save", methods=["POST"])
@login_required
def page_view_save():
    """Saves a named AppManagerPageView (filter + sort + columns)."""
    import json
    from arasCore.admin.models import AppManagerPageView, AppManagerTable
    data = request.get_json() or {}
    
    table_id = data.get("table_id")
    name     = data.get("name")
    label    = data.get("label") or name
    
    if not table_id or not name:
        return jsonify({"ok": False, "error": "Missing table_id or name"}), 400
        
    try:
        view = AppManagerPageView.query.filter_by(
            table_id=table_id, name=name, owner_id=current_user.id
        ).first()
        
        if not view:
            view = AppManagerPageView(
                table_id=table_id, name=name, label=label, owner_id=current_user.id
            )
            db.session.add(view)
            
        view.filter_json = json.dumps(data.get("filter", {}))
        view.sort_json   = json.dumps(data.get("sort", {}))
        view.columns_csv = ",".join(data.get("columns", []))
        view.is_shared   = bool(data.get("is_shared"))
        
        db.session.commit()
        return jsonify({"ok": True, "view_id": view.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
