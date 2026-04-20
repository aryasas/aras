# -*- coding: utf-8 -*-
"""
arasCore/arasAdmin/services.py
Dynamic app loader + model/form factory.
Migrated from app_manager/loader.py + app_manager/factory.py.
"""
import logging
from flask import Blueprint
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, IntegerField, BooleanField, DateField, FloatField
from wtforms.validators import DataRequired, Optional

from arasCore.lib.extensions import db

logger = logging.getLogger(__name__)


# ── Column type map ───────────────────────────────────────────────────────────

def _make_sa_column(col):
    """Build a SQLAlchemy Column from an AppManagerColumn instance."""
    ft = col.field_type
    nullable = not col.required
    unique = getattr(col, "unique", False)
    max_len = getattr(col, "max_length", None) or col.length or 200
    if ft == "string":
        return db.Column(db.String(max_len), nullable=nullable, unique=unique)
    if ft in ("email", "phone"):
        return db.Column(db.String(max_len), nullable=nullable, unique=unique)
    if ft == "url":
        return db.Column(db.String(500), nullable=nullable)
    if ft in ("select", "uuid"):
        return db.Column(db.String(100), nullable=nullable)
    if ft in ("file", "image"):
        return db.Column(db.String(500), nullable=nullable)
    if ft == "text":
        return db.Column(db.Text, nullable=nullable)
    if ft == "integer":
        return db.Column(db.Integer, nullable=nullable)
    if ft == "float":
        return db.Column(db.Float, nullable=nullable)
    if ft == "decimal":
        return db.Column(db.Numeric(10, 2), nullable=nullable)
    if ft == "boolean":
        return db.Column(db.Boolean, default=False)
    if ft == "date":
        return db.Column(db.Date, nullable=nullable)
    if ft == "datetime":
        return db.Column(db.DateTime, nullable=nullable)
    if ft == "json":
        return db.Column(db.JSON, nullable=nullable)
    if ft == "relation":
        if col.relation_table_id:
            return None  # handled in make_table_model
        if col.relation_system_table:
            fk = f"{col.relation_system_table}.id"
            return db.Column(db.Integer, db.ForeignKey(fk), nullable=nullable)
    return db.Column(db.String(200), nullable=nullable)


def _make_wtf_field(col):
    """Build a WTForms field from an AppManagerColumn instance."""
    from wtforms.validators import DataRequired, Optional as Opt, Email, URL, Length, NumberRange
    validators = [DataRequired()] if col.required else [Opt()]

    max_len = getattr(col, "max_length", None)
    if max_len:
        validators.append(Length(max=max_len))

    min_v = getattr(col, "min_value", None)
    max_v = getattr(col, "max_value", None)
    if min_v is not None or max_v is not None:
        try:
            validators.append(NumberRange(
                min=float(min_v) if min_v else None,
                max=float(max_v) if max_v else None,
            ))
        except (TypeError, ValueError):
            pass

    render_kw = {}
    placeholder = getattr(col, "placeholder", None)
    if placeholder:
        render_kw["placeholder"] = placeholder

    description = getattr(col, "help_text", None) or ""

    ft = col.field_type
    if ft == "text":
        return TextAreaField(col.label, validators=validators,
                             render_kw=render_kw, description=description)
    if ft == "integer":
        return IntegerField(col.label, validators=validators,
                            render_kw=render_kw, description=description)
    if ft in ("float", "decimal"):
        from wtforms import DecimalField
        return DecimalField(col.label, validators=validators,
                            render_kw=render_kw, description=description)
    if ft == "boolean":
        return BooleanField(col.label, description=description)
    if ft == "date":
        return DateField(col.label, validators=validators,
                         render_kw=render_kw, description=description)
    if ft == "datetime":
        from wtforms.fields import DateTimeLocalField
        return DateTimeLocalField(col.label, validators=validators,
                                  render_kw=render_kw, description=description)
    if ft == "email":
        from wtforms.fields import EmailField
        validators.append(Email())
        return EmailField(col.label, validators=validators,
                          render_kw=render_kw, description=description)
    if ft == "url":
        from wtforms.fields import URLField
        validators.append(URL())
        return URLField(col.label, validators=validators,
                        render_kw=render_kw, description=description)
    if ft == "select":
        choices_str = getattr(col, "choices", "") or ""
        opts = [(c.strip(), c.strip()) for c in choices_str.split(",") if c.strip()]
        from wtforms import SelectField as SF
        return SF(col.label, choices=opts, validators=validators, description=description)
    if ft == "relation":
        from wtforms import SelectField as SF
        return SF(col.label, coerce=int, validators=validators, description=description)
    if ft in ("file", "image"):
        from wtforms import FileField as FF
        return FF(col.label, description=description)
    if ft == "json":
        return TextAreaField(col.label, validators=validators,
                             render_kw=render_kw, description=description)
    return StringField(col.label, validators=validators,
                       render_kw=render_kw, description=description)


# In-process cache:  key = db_table_name  ->  (DynamicModel, DynamicForm, view_columns)
_table_registry: dict = {}


def clear_cache(app_name=None):
    """Clear cached models/forms for an app or all apps."""
    if app_name:
        keys = [k for k in _table_registry if k.startswith(f"ab_{app_name}_") or k == f"ab_{app_name}"]
        for k in keys:
            _table_registry.pop(k, None)
    else:
        _table_registry.clear()


def make_table_model(tbl, app_name, all_tables_in_app=None):
    """
    Build a SQLAlchemy Model for one AppManagerTable.
    all_tables_in_app: list of AppManagerTable in same app, used to resolve FK targets.
    """
    db_tname   = tbl.get_db_table_name(app_name)
    class_name = f"DynModel_{db_tname}"

    if db_tname in _table_registry:
        return _table_registry[db_tname][0]

    # Check SA mapper registry
    try:
        existing = db.Model.registry._class_registry.get(class_name)
    except Exception:
        existing = None
    if existing is not None:
        _table_registry.setdefault(db_tname, (existing, None, []))
        return existing

    attrs = {
        "__tablename__":   db_tname,
        "__table_args__":  {"extend_existing": True},
        "id":              db.Column(db.Integer, primary_key=True),
    }

    columns = tbl.get_columns()
    # index other tables by id for FK resolution
    tbl_map = {t.id: t for t in (all_tables_in_app or [])}

    for col in columns:
        if col.field_type == "relation" and col.relation_table_id and col.relation_table_id in tbl_map:
            target_tbl  = tbl_map[col.relation_table_id]
            target_name = target_tbl.get_db_table_name(app_name)
            fk_col_name = f"{col.name}_id"
            attrs[fk_col_name] = db.Column(
                db.Integer, db.ForeignKey(f"{target_name}.id"),
                nullable=not col.required
            )
            # relationship attribute
            rel_class_name = f"DynModel_{target_name}"
            # many-to-one: delete-orphan requires single_parent; use save-update only
            attrs[col.name] = db.relationship(
                rel_class_name, foreign_keys=f"[{class_name}.{fk_col_name}]",
                lazy="select",
            )
        else:
            sa_col = _make_sa_column(col)
            if sa_col is not None:
                attrs[col.name] = sa_col

    def __repr__(self):
        return f"<{tbl.name} id={self.id}>"

    attrs["__repr__"] = __repr__

    DynModel = type(class_name, (db.Model,), attrs)
    _table_registry[db_tname] = (DynModel, None, [])
    logger.info(f"[services] Model created: {class_name}")
    return DynModel


def make_table_form(tbl, model_cls, app_id):
    """Build a WTForms Form for one AppManagerTable."""
    db_tname = model_cls.__tablename__ if model_cls is not None else str(tbl.id)
    form_key = f"form_{db_tname}"

    cached = _table_registry.get(db_tname)
    if cached and cached[1] is not None:
        return cached[1]

    form_attrs = {}
    for col in tbl.get_columns():
        if col.field_type == "relation" and col.relation_table_id:
            # populate choices at runtime; store as SelectField with lazy choices
            from wtforms import SelectField as SF
            from wtforms.validators import Optional as Opt
            field = SF(col.label, coerce=int, validators=[Opt()])
            form_attrs[f"{col.name}_id"] = field
        else:
            form_attrs[col.name] = _make_wtf_field(col)

    DynForm = type(f"{tbl.name.capitalize()}Form", (FlaskForm,), form_attrs)

    if db_tname in _table_registry:
        m, _, v = _table_registry[db_tname]
        _table_registry[db_tname] = (m, DynForm, v)

    logger.info(f"[services] Form created: {DynForm.__name__}")
    return DynForm


def get_view_columns(tbl):
    """[('Label', 'col_name'), ...] — skip relation objects, use FK id col."""
    vcols = []
    for col in tbl.get_columns():
        if col.field_type == "relation" and col.relation_table_id:
            vcols.append((col.label, f"{col.name}_id"))
        else:
            vcols.append((col.label, col.name))
    return vcols


def build_sidebar_menu():
    """
    Return sidebar menu tree gabungan dari:
    1. Code-based apps — dari _helper_registry (manifest.py tiap app)
    2. Dynamic apps    — dari AppManagerApp yang active di DB

    Structure setiap item:
      {title, icon, order, children: [{title, icon, url, children: [...]}]}
    """
    result = []

    # ── 1. Code-based apps dari manifest registry ─────────────────────────────
    try:
        from arasCore.lib.blueprints import get_helper_registry
        for helper in sorted(get_helper_registry().values(), key=lambda h: h.admin_order):
            result.append(helper.to_menu_dict())
    except Exception as e:
        logger.warning(f"[services] manifest menu error: {e}")

    # ── 2. Dynamic apps dari DB ───────────────────────────────────────────────
    def _node_to_dict(node, app_url, app_name):
        t = node["tbl"]
        full_url = t.get_full_url(app_url)
        return {
            "title":    t.get_menu_title(),
            "icon":     t.menu_icon or "fa-table",
            "url":      f"/admin{full_url}/",
            "children": [_node_to_dict(c, app_url, app_name) for c in node["children"]],
        }

    try:
        from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
        apps = AppManagerApp.query.filter_by(is_active=True).order_by(AppManagerApp.menu_order).all()
        for app in apps:
            tables = (
                AppManagerTable.query
                .filter_by(app_id=app.id, is_active=True, show_in_menu=True)
                .order_by(AppManagerTable.menu_order)
                .all()
            )
            tbl_map = {t.id: {"tbl": t, "children": []} for t in tables}
            roots = []
            for t in tables:
                node = tbl_map[t.id]
                if t.parent_table_id and t.parent_table_id in tbl_map:
                    tbl_map[t.parent_table_id]["children"].append(node)
                else:
                    roots.append(node)
            result.append({
                "title":    app.main_title,
                "icon":     app.icon or "fa-cubes",
                "order":    app.menu_order or 99,
                "children": [_node_to_dict(n, app.url, app.name) for n in roots],
                "source":   "dynamic",
            })
    except Exception as e:
        logger.warning(f"[services] dynamic menu error: {e}")

    return sorted(result, key=lambda x: x.get("order", 99))


# ── Loader ────────────────────────────────────────────────────────────────────

def _register_built_app(app_def_id, flask_app):
    """Register one AppManagerApp (all its tables) as a single Flask blueprint."""
    with flask_app.app_context():
        try:
            from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
            app_def = AppManagerApp.query.get(app_def_id)
            if not app_def:
                logger.warning(f"[services] app_def id={app_def_id} not found.")
                return False

            # Sort tables: parents before children (topological)
            all_tbls = app_def.get_tables()
            ordered, seen = [], set()

            def _visit(t):
                if t.id in seen:
                    return
                if t.parent_table_id:
                    parent = next((x for x in all_tbls if x.id == t.parent_table_id), None)
                    if parent:
                        _visit(parent)
                seen.add(t.id)
                ordered.append(t)

            for t in all_tbls:
                _visit(t)

            # Build models (parents first so FK refs resolve)
            table_models = {}
            for tbl in ordered:
                model = make_table_model(tbl, app_def.name, all_tbls)
                model.__table__.create(db.engine, checkfirst=True)
                table_models[tbl.id] = model

            # Snapshot everything needed outside DB session
            app_name       = app_def.name
            app_url        = app_def.url
            app_main_title = app_def.main_title
            app_in_sidebar = app_def.in_sidebar

            table_snapshots = []
            for tbl in ordered:
                if not tbl.is_active:
                    continue
                form_cls  = make_table_form(tbl, table_models[tbl.id], app_def.id)
                vcols     = get_view_columns(tbl)
                full_url  = tbl.get_full_url(app_url)
                menu_tit  = tbl.get_menu_title()
                tbl_name  = tbl.name
                table_snapshots.append({
                    "name":       tbl_name,
                    "title":      tbl.title,
                    "menu_title": menu_tit,
                    "url":        full_url,
                    "model":      table_models[tbl.id],
                    "form":       form_cls,
                    "vcols":      vcols,
                    "app_title":  app_def.title,
                    "app_id":     app_def.id,
                })

        except Exception as e:
            logger.error(f"[services] Error loading app_def id={app_def_id}: {e}", exc_info=True)
            return False

    try:
        bp_name = f"ab_{app_name}"
        if bp_name in flask_app.blueprints:
            logger.info(f"[services] Blueprint already registered: {bp_name}, skip.")
            return True

        bp = Blueprint(bp_name, __name__)

        for snap in table_snapshots:
            _register_table_routes(bp, snap, table_snapshots)

        flask_app.register_blueprint(bp)
        logger.info(f"[services] Registered app '{app_name}' with {len(table_snapshots)} table(s).")
        return True

    except Exception as e:
        logger.error(f"[services] Failed to register {app_name}: {e}", exc_info=True)
        return False


def _register_table_routes(bp, snap, all_snaps):
    """Add CRUD + API routes for one table into blueprint bp."""
    model     = snap["model"]
    form_cls  = snap["form"]
    title     = snap["title"]
    main_t    = snap["menu_title"]
    burl      = snap["url"]      # e.g. /inventory/products
    tname     = snap["name"]     # e.g. products
    vcols     = snap["vcols"]
    app_title = snap["app_title"]
    app_id    = snap["app_id"]
    # Sibling table links for submenu: [(title, url), ...]
    sibling_tabs = [(s["title"], s["url"]) for s in all_snaps]

    # ── helpers ──────────────────────────────────────────────────────────────

    # Admin view helpers (login_required, admin/ab_*.html templates)

    def make_adm_list(model, title, main_t, vcols, adm_burl, app_title, app_id, sibling_tabs, cur_burl):
        from flask import render_template
        from flask_login import login_required
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]

        @login_required
        def view():
            items = model.query.all()
            return render_template(
                "admin/ab_list.html",
                title=title, main_title=main_t,
                items=items, view_columns=vcols,
                add_url=f"{adm_burl}/add/",
                edit_url_base=adm_burl,
                delete_url_base=adm_burl,
                app_title=app_title, app_id=app_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_adm_add(model, form_cls, title, main_t, adm_burl, app_title, app_id, sibling_tabs, cur_burl):
        from flask import render_template, redirect, flash
        from flask_login import login_required
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]

        @login_required
        def view():
            form = form_cls()
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                obj = model()
                form.populate_obj(obj)
                db.session.add(obj)
                db.session.commit()
                flash("Record added.", "success")
                return redirect(f"{adm_burl}/")
            return render_template(
                "admin/ab_form.html",
                title=f"Add — {title}", main_title=main_t,
                form=form, action=f"{adm_burl}/add/", list_url=f"{adm_burl}/",
                app_title=app_title, app_id=app_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_adm_edit(model, form_cls, title, main_t, adm_burl, app_title, app_id, sibling_tabs, cur_burl):
        from flask import render_template, redirect, flash
        from flask_login import login_required
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]

        @login_required
        def view(item_id):
            obj  = model.query.get_or_404(item_id)
            form = form_cls(obj=obj)
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                form.populate_obj(obj)
                db.session.commit()
                flash("Record updated.", "success")
                return redirect(f"{adm_burl}/")
            return render_template(
                "admin/ab_form.html",
                title=f"Edit — {title}", main_title=main_t,
                form=form, action=f"{adm_burl}/{item_id}/", list_url=f"{adm_burl}/",
                app_title=app_title, app_id=app_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_adm_delete(model, adm_burl):
        from flask import redirect, flash
        from flask_login import login_required

        @login_required
        def view(item_id):
            obj = model.query.get_or_404(item_id)
            db.session.delete(obj)
            db.session.commit()
            flash("Record deleted.", "warning")
            return redirect(f"{adm_burl}/")
        return view

    # Web view helpers (public read, login_required for write, web templates)

    def make_web_list(model, title, main_t, vcols, burl, app_title, sibling_tabs, cur_burl):
        from flask import render_template

        def view():
            items = model.query.all()
            return render_template(
                "admin/ab_web_list.html",
                title=title, main_title=main_t,
                items=items, view_columns=vcols,
                add_url=f"{burl}/add/",
                edit_url_base=burl,
                delete_url_base=burl,
                app_title=app_title,
                sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_web_add(model, form_cls, title, main_t, burl, app_title, sibling_tabs, cur_burl):
        from flask import render_template, redirect, flash
        from flask_login import login_required

        @login_required
        def view():
            form = form_cls()
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                obj = model()
                form.populate_obj(obj)
                db.session.add(obj)
                db.session.commit()
                flash("Record added.", "success")
                return redirect(f"{burl}/")
            return render_template(
                "admin/ab_web_form.html",
                title=f"Add — {title}", main_title=f"Add {main_t}",
                form=form, action=f"{burl}/add/", list_url=f"{burl}/",
                app_title=app_title,
                sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_web_edit(model, form_cls, title, main_t, burl, app_title, sibling_tabs, cur_burl):
        from flask import render_template, redirect, flash
        from flask_login import login_required

        @login_required
        def view(item_id):
            obj  = model.query.get_or_404(item_id)
            form = form_cls(obj=obj)
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                form.populate_obj(obj)
                db.session.commit()
                flash("Record updated.", "success")
                return redirect(f"{burl}/")
            return render_template(
                "admin/ab_web_form.html",
                title=f"Edit — {title}", main_title=f"Edit {main_t}",
                form=form, action=f"{burl}/{item_id}/", list_url=f"{burl}/",
                app_title=app_title,
                sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_web_delete(model, burl):
        from flask import redirect, flash
        from flask_login import login_required

        @login_required
        def view(item_id):
            obj = model.query.get_or_404(item_id)
            db.session.delete(obj)
            db.session.commit()
            flash("Record deleted.", "warning")
            return redirect(f"{burl}/")
        return view

    # ── register ─────────────────────────────────────────────────────────────
    ep      = tname          # endpoint prefix, e.g. "products"
    adm_url = f"/admin{burl}"  # admin route prefix, e.g. /admin/inventory/products

    # Web (public) routes
    bp.add_url_rule(f"{burl}/",               endpoint=f"{ep}_index",      view_func=make_web_list(model, title, main_t, vcols, burl, app_title, sibling_tabs, burl))
    bp.add_url_rule(f"{burl}/add/",           endpoint=f"{ep}_add",        view_func=make_web_add(model, form_cls, title, main_t, burl, app_title, sibling_tabs, burl),  methods=["GET","POST"])
    bp.add_url_rule(f"{burl}/<int:item_id>/", endpoint=f"{ep}_edit",       view_func=make_web_edit(model, form_cls, title, main_t, burl, app_title, sibling_tabs, burl), methods=["GET","POST"])
    bp.add_url_rule(f"{burl}/<int:item_id>/delete/", endpoint=f"{ep}_delete", view_func=make_web_delete(model, burl), methods=["POST"])

    # Admin routes
    bp.add_url_rule(f"{adm_url}/",               endpoint=f"{ep}_adm_index",  view_func=make_adm_list(model, title, main_t, vcols, adm_url, app_title, app_id, sibling_tabs, adm_url))
    bp.add_url_rule(f"{adm_url}/add/",           endpoint=f"{ep}_adm_add",    view_func=make_adm_add(model, form_cls, title, main_t, adm_url, app_title, app_id, sibling_tabs, adm_url),  methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/", endpoint=f"{ep}_adm_edit",   view_func=make_adm_edit(model, form_cls, title, main_t, adm_url, app_title, app_id, sibling_tabs, adm_url), methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/delete/", endpoint=f"{ep}_adm_delete", view_func=make_adm_delete(model, adm_url), methods=["POST"])

    # Register ke universal API — handler ada di api_handler.py, bukan di sini
    try:
        from arasCore.lib.api_handler import register_api_model
        register_api_model(burl.strip("/"), model)
    except Exception as _e:
        logger.warning(f"[services] api_handler register skipped: {_e}")


def _populate_relation_choices(form, model):
    """Fill SelectField choices for FK relation fields at request time."""
    from sqlalchemy import inspect as sa_inspect
    for field in form:
        if hasattr(field, 'coerce') and field.name.endswith("_id"):
            # Find the related model via FK
            try:
                fk = list(model.__table__.c[field.name].foreign_keys)[0]
                ref_table = fk.column.table
                ref_model = None
                for mapper in db.Model.registry.mappers:
                    if mapper.local_table.name == ref_table.name:
                        ref_model = mapper.class_
                        break
                if ref_model:
                    rows = ref_model.query.all()
                    choices = [(0, "— Select —")]
                    for row in rows:
                        label = getattr(row, "name", None) or getattr(row, "title", None) or getattr(row, "username", None) or str(row.id)
                        choices.append((row.id, label))
                    field.choices = choices
            except Exception:
                field.choices = [(0, "— Select —")]


def load_all_built_apps(flask_app):
    """Load all active AppManagerApp records and register them as blueprints."""
    try:
        from arasCore.arasAdmin.models import AppManagerApp
        with flask_app.app_context():
            db.create_all()
            apps = AppManagerApp.query.filter_by(is_active=True).all()
            app_ids = [a.id for a in apps]
            logger.info(f"[services] Found {len(app_ids)} active built app(s).")

        for app_id in app_ids:
            _register_built_app(app_id, flask_app)

    except Exception as e:
        logger.warning(f"[services] Could not load built apps: {e}")


# ── Dashboard Widgets ─────────────────────────────────────────────────────────

def get_dashboard_widgets(user):
    """
    Return a list of widget dicts for the admin dashboard.
    Each widget: {id, title, value, icon, color, link, link_label}
    """
    # from arasCore.arasAdmin.models import Post, Message, UserActivity, Notification
    from arasCore.arasAdmin.models import UserActivity, Notification
    from arasCore.auth import User
    from arasCore.auth import User
    from arasCore.permissions import UserRole

    widgets = []

    try:
        total_users = User.query.count()
        widgets.append({
            "id":         "total_users",
            "title":      "Total Users",
            "value":      total_users,
            "icon":       "fa fa-users",
            "color":      "primary",
            "link":       "/admin/users",
            "link_label": "View all",
        })
    except Exception:
        pass

    # try:
    #     total_posts = Post.query.count()
    #     widgets.append({
    #         "id":         "total_posts",
    #         "title":      "Total Posts",
    #         "value":      total_posts,
    #         "icon":       "fa fa-file-text",
    #         "color":      "success",
    #         "link":       "/admin/explore",
    #         "link_label": "Explore",
    #     })
    # except Exception:
    #     pass

    # try:
    #     unread_msg = user.new_messages() if hasattr(user, "new_messages") else 0
    #     widgets.append({
    #         "id":         "unread_messages",
    #         "title":      "Unread Messages",
    #         "value":      unread_msg,
    #         "icon":       "fa fa-envelope",
    #         "color":      "warning",
    #         "link":       "/admin/messages",
    #         "link_label": "Open inbox",
    #     })
    # except Exception:
    #     pass

    try:
        unread_act = user.new_activities() if hasattr(user, "new_activities") else 0
        widgets.append({
            "id":         "new_activities",
            "title":      "New Log Entries",
            "value":      unread_act,
            "icon":       "fa fa-bolt",
            "color":      "info",
            "link":       "/admin/user-log",
            "link_label": "View log",
        })
    except Exception:
        pass

    try:
        from arasCore.arasAdmin.models import AppManagerApp
        total_apps = AppManagerApp.query.filter_by(is_active=True).count()
        widgets.append({
            "id":         "active_apps",
            "title":      "Active Apps",
            "value":      total_apps,
            "icon":       "fa fa-cubes",
            "color":      "secondary",
            "link":       "/admin/apps",
            "link_label": "Manage",
        })
    except Exception:
        pass

    return widgets
