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


def _slug_from_url(url: str) -> str:
    """Derive admin URL segment from app url. '/todo-test' → 'todo-test'."""
    return url.strip("/") or "app"


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


def apply_search_and_filters(query, model, search_cols, request):
    """
    Apply search (q=) and multi-row filters (f_col[], f_op[], f_val[]) to a query.

    search_cols: list of column names to search against (from mgr_column.searchable or caller).
    Returns: (query, active_filters_list) where active_filters_list is for template rendering.
    """
    import sqlalchemy as _sa

    active_filters = []

    # ── search ────────────────────────────────────────────────────────────────
    q = request.args.get("q", "").strip()
    if q and search_cols:
        from sqlalchemy import or_
        clauses = []
        for col_name in search_cols:
            col = getattr(model, col_name, None)
            if col is not None:
                try:
                    clauses.append(col.ilike(f"%{q}%"))
                except Exception:
                    pass
        if clauses:
            query = query.filter(or_(*clauses))

    # ── filters ───────────────────────────────────────────────────────────────
    cols  = request.args.getlist("f_col[]")
    ops   = request.args.getlist("f_op[]")
    vals  = request.args.getlist("f_val[]")

    for col_name, op, val in zip(cols, ops, vals):
        col_name = col_name.strip()
        op       = op.strip()
        val      = val.strip()
        if not col_name or not op:
            continue
        col_attr = getattr(model, col_name, None)
        if col_attr is None:
            continue
        try:
            if op == "equals":
                query = query.filter(col_attr == val)
            elif op == "not_equals":
                query = query.filter(col_attr != val)
            elif op == "like":
                query = query.filter(col_attr.ilike(f"%{val}%"))
            elif op == "not_like":
                query = query.filter(col_attr.notilike(f"%{val}%"))
            elif op == "in":
                items = [v.strip() for v in val.split(",") if v.strip()]
                query = query.filter(col_attr.in_(items))
            elif op == "not_in":
                items = [v.strip() for v in val.split(",") if v.strip()]
                query = query.filter(col_attr.notin_(items))
            elif op == "is":
                query = query.filter(col_attr.is_(None))
                val = ""
            active_filters.append({"col": col_name, "op": op, "val": val})
        except Exception:
            pass

    return query, active_filters, q


def _invoke_hooks(obj, is_new: bool):
    """Return (before_hook, after_hook) callables for ArasModel hooks + audit log."""
    from arasCore.lib.audit import maybe_log, _snapshot
    before_snap = None if is_new else _snapshot(obj)
    action = "create" if is_new else "update"

    def _before():
        fn = getattr(obj, "before_save", None)
        if callable(fn):
            fn(is_new=is_new)

    def _after():
        fn = getattr(obj, "after_save", None)
        if callable(fn):
            fn(is_new=is_new)
        maybe_log(obj, action=action, before=before_snap, after=_snapshot(obj))

    return _before, _after


def sync_table_columns(model):
    """ALTER TABLE to add any SA model columns missing from the physical DB table."""
    tname = model.__tablename__
    try:
        existing = {row[0] for row in db.session.execute(db.text(f"DESCRIBE `{tname}`")).fetchall()}
    except Exception:
        return
    for col in model.__table__.columns:
        if col.name in existing:
            continue
        try:
            col_def = col.type.compile(dialect=db.engine.dialect)
            nullable = "" if col.nullable is False else " NULL"
            db.session.execute(db.text(f"ALTER TABLE `{tname}` ADD COLUMN `{col.name}` {col_def}{nullable}"))
            db.session.commit()
            logger.info(f"[services] ALTER TABLE {tname} ADD COLUMN {col.name}")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"[services] Could not add column {col.name} to {tname}: {e}")


def clear_cache(app_name=None):
    """Clear cached models/forms + SA mapper entries so models rebuild on next request."""
    try:
        from arasCore.lib.audit import invalidate_cache as _audit_invalidate
        _audit_invalidate()
    except Exception:
        pass
    if app_name:
        safe = app_name.replace("-", "_")
        keys = [k for k in _table_registry if k.startswith(f"{safe}_") or k == safe]
    else:
        keys = list(_table_registry.keys())

    for k in keys:
        # Remove from SA mapper registry so make_table_model rebuilds the class
        class_name = f"DynModel_{k}"
        try:
            reg = db.Model.registry._class_registry
            reg.pop(class_name, None)
        except Exception:
            pass
        # Remove SA Table from metadata so columns are refreshed
        try:
            if k in db.metadata.tables:
                db.metadata.remove(db.metadata.tables[k])
        except Exception:
            pass
        _table_registry.pop(k, None)


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

    cached = _table_registry.get(db_tname)
    if cached and cached[1] is not None:
        return cached[1]

    from arasCore.lib.forms import build_form_from_table
    DynForm = build_form_from_table(tbl)

    if db_tname in _table_registry:
        m, _, v = _table_registry[db_tname]
        _table_registry[db_tname] = (m, DynForm, v)

    logger.info(f"[services] Form created: {DynForm.__name__}")
    return DynForm


def get_view_columns(tbl):
    """[('Label', 'col_name'), ...] — respects list_columns order and show_in_list flag."""
    all_cols = tbl.get_columns()

    # Build lookup by name
    col_map = {}
    for col in all_cols:
        key = f"{col.name}_id" if (col.field_type == "relation" and col.relation_table_id) else col.name
        col_map[col.name] = (col.label, key, col)

    # If list_columns CSV is set, use that order and selection
    if tbl.list_columns:
        names = [n.strip() for n in tbl.list_columns.split(",") if n.strip()]
        vcols = []
        for name in names:
            if name in col_map:
                label, field_key, _ = col_map[name]
                vcols.append((label, field_key))
        return vcols

    # Otherwise fall back to show_in_list flag (or all if none explicitly set)
    visible = [c for c in all_cols if c.show_in_list]
    if not visible:
        visible = all_cols
    vcols = []
    for col in visible:
        if col.field_type == "relation" and col.relation_table_id:
            vcols.append((col.label, f"{col.name}_id"))
        else:
            vcols.append((col.label, col.name))
    return vcols


def _build_raw_menu() -> list:
    """Build the raw sidebar menu tree (no RBAC filter). Suitable for caching."""
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
        from arasCore.lib.blueprints import get_helper_registry
        manifest_names = set(get_helper_registry().keys())
    except Exception:
        manifest_names = set()

    try:
        from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
        apps = AppManagerApp.query.filter_by(is_active=True).order_by(AppManagerApp.menu_order).all()
        for app in apps:
            if app.name in manifest_names:
                continue
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
            adm_slug = _slug_from_url(app.url)
            children = [_node_to_dict(n, app.url, app.name) for n in roots]
            children.append({
                "title":    "Settings",
                "icon":     "fa-cog",
                "url":      f"/admin/{adm_slug}/settings/",
                "children": [],
            })
            result.append({
                "title":    app.main_title,
                "icon":     app.icon or "fa-cubes",
                "order":    app.menu_order or 99,
                "url":      f"/admin/{adm_slug}/",
                "children": children,
                "source":   "dynamic",
                "app_slug": adm_slug,
            })
    except Exception as e:
        logger.warning(f"[services] dynamic menu error: {e}")

    return sorted(result, key=lambda x: x.get("order", 99))


def build_sidebar_menu() -> list:
    """
    Return sidebar menu tree (code-based + dynamic apps), filtered by RBAC.
    Raw tree is cached for 60 s; per-user RBAC filter runs every request.
    """
    try:
        from arasCore.lib.extensions import cache as _cache
        raw = _cache.get("_sidebar_raw")
        if raw is None:
            raw = _build_raw_menu()
            _cache.set("_sidebar_raw", raw, timeout=60)
    except Exception:
        raw = _build_raw_menu()

    try:
        from flask_login import current_user
        if current_user.is_authenticated:
            return _filter_menu_for_user(raw, current_user)
    except Exception:
        pass
    return raw


def _filter_menu_for_user(menu_items, user):
    """Remove apps/pages the user has no 'view' permission for."""
    from arasCore.rbac import get_user_allowed_resources

    filtered = []
    for item in menu_items:
        # Derive app_slug from item structure
        app_slug = item.get("name") or item.get("app_slug")
        if not app_slug:
            # Fallback: try to parse from URL /admin/{app_slug}/
            url = item.get("url", "")
            parts = url.strip("/").split("/")
            app_slug = parts[1] if len(parts) >= 2 and parts[0] == "admin" else None

        if not app_slug:
            filtered.append(item)
            continue

        allowed = get_user_allowed_resources(user, app_slug)
        if allowed is None:
            # None = no restriction (RBAC off or admin/wildcard)
            filtered.append(item)
            continue

        # Filter children to only permitted resources
        children = item.get("children", [])
        visible_children = []
        for child in children:
            child_url = child.get("url", "")
            # Extract resource slug from URL: /admin/{app}/{resource}/
            c_parts = child_url.strip("/").split("/")
            # c_parts: ["admin", app_slug, resource_slug, ...]
            res_slug = "/".join(c_parts[2:]) if len(c_parts) >= 3 else None
            if res_slug is None or res_slug in allowed:
                visible_children.append(child)
            # Always keep nested MenuGroups (they have children of their own)
            elif child.get("children"):
                sub_children = [
                    sc for sc in child["children"]
                    if (lambda u: "/".join(u.strip("/").split("/")[2:]) or None)(sc.get("url", "")) in allowed
                ]
                if sub_children:
                    visible_children.append({**child, "children": sub_children})

        if visible_children:
            filtered.append({**item, "children": visible_children})
        elif allowed:
            # User has some permissions but none visible as children — still show app entry
            filtered.append({**item, "children": []})
        # else: user has no permissions at all for this app — skip it

    return filtered


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
                sync_table_columns(model)
                table_models[tbl.id] = model

            # Snapshot everything needed outside DB session
            app_name       = app_def.name
            app_url        = app_def.url
            app_main_title = app_def.main_title
            # admin_slug is derived from url so /admin/<slug>/ always matches the app's url
            admin_slug     = _slug_from_url(app_url)

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
                    "name":               tbl_name,
                    "title":              tbl.title,
                    "menu_title":         menu_tit,
                    "url":                full_url,
                    "model":              table_models[tbl.id],
                    "form":               form_cls,
                    "vcols":              vcols,
                    "app_title":          app_def.title,
                    "app_id":             app_def.id,
                    "table_id":           tbl.id,
                    "parent_table_id":    tbl.parent_table_id,
                    "app_slug":           admin_slug,
                    "required_role_slug": tbl.required_role_slug,
                    "per_page":           tbl.per_page or 20,
                })

        except Exception as e:
            logger.error(f"[services] Error loading app_def id={app_def_id}: {e}", exc_info=True)
            return False

    try:
        # Blueprint name must be a valid Python identifier — replace hyphens with underscores.
        # The URL slug (admin_slug) keeps hyphens for the actual URL paths.
        bp_safe = f"mgr_{admin_slug.replace('-', '_')}"

        # Collect all blueprint prefixes to purge (safe name + any timestamped variants)
        stale_bp_prefixes = {
            bp_key + "."
            for bp_key in list(flask_app.blueprints.keys())
            if bp_key == bp_safe or bp_key.startswith(bp_safe + "_")
        }
        for bp_key in list(flask_app.blueprints.keys()):
            if bp_key == bp_safe or bp_key.startswith(bp_safe + "_"):
                flask_app.blueprints.pop(bp_key)

        stale_rules = [
            r for r in flask_app.url_map._rules
            if any(r.endpoint.startswith(pfx) for pfx in stale_bp_prefixes)
        ]
        if stale_rules:
            for rule in stale_rules:
                flask_app.url_map._rules.remove(rule)
                flask_app.url_map._rules_by_endpoint.pop(rule.endpoint, None)
                flask_app.view_functions.pop(rule.endpoint, None)
            flask_app.url_map.update()
            logger.info(f"[services] Purged {len(stale_rules)} stale route(s) for '{admin_slug}'.")

        bp_name = bp_safe if bp_safe not in flask_app.blueprints else f"{bp_safe}_{__import__('time').time_ns()}"

        bp = Blueprint(bp_name, __name__)

        for snap in table_snapshots:
            _register_table_routes(bp, snap, table_snapshots)

        # Auto-mount /admin/<admin_slug>/settings/
        try:
            from arasCore.arasAdmin.settings_service import mount_settings_route
            mount_settings_route(
                bp, admin_slug, app_main_title,
                schema=[], is_dynamic=True,
                endpoint=f"settings_{admin_slug}",
                registry_key=app_name,
            )
        except Exception as _se:
            logger.warning(f"[services] settings mount failed for {admin_slug}: {_se}")

        # Auto-mount /admin/<admin_slug>/ home
        try:
            from arasCore.arasAdmin.home_service import mount_home_route
            mount_home_route(
                bp, admin_slug, app_main_title,
                is_dynamic=True,
                endpoint=f"home_{admin_slug}",
                registry_key=app_name,
            )
        except Exception as _he:
            logger.warning(f"[services] home mount failed for {admin_slug}: {_he}")

        # Public app root: redirect /<app>/ → first table URL
        if table_snapshots:
            first_url = table_snapshots[0]["url"] + "/"

            def make_app_index(target=first_url):
                from flask import redirect as _redir
                def view():
                    return _redir(target)
                return view

            try:
                bp.add_url_rule(
                    f"{app_url}/",
                    endpoint=f"{app_name}_pub_index",
                    view_func=make_app_index(),
                )
            except Exception as _ie:
                logger.debug(f"[services] pub index already registered for {app_name}: {_ie}")

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
    table_id  = snap["table_id"]
    app_slug  = snap.get("app_slug", "")
    req_role  = snap.get("required_role_slug")
    # Sibling table links for submenu: [(title, url), ...]
    sibling_tabs = [(s["title"], s["url"]) for s in all_snaps]

    # Child tables: snaps whose parent_table_id == current table_id
    cur_table_id = snap.get("table_id")
    child_snaps = [
        s for s in all_snaps
        if s.get("parent_table_id") and s["parent_table_id"] == cur_table_id
    ]
    # Build child defs: detect FK column name on child model pointing to parent model
    child_defs = []
    for cs in child_snaps:
        fk_col = _detect_parent_fk(cs["model"], model)
        if fk_col:
            child_defs.append({
                "title":   cs["title"],
                "model":   cs["model"],
                "vcols":   cs["vcols"],
                "adm_url": f"/admin{cs['url']}",
                "fk_col":  fk_col,
            })

    # ── helpers ──────────────────────────────────────────────────────────────

    # Admin view helpers (login_required, admin/ab_*.html templates)

    def make_adm_list(model, title, main_t, vcols, adm_burl, app_title, app_id, table_id, sibling_tabs, cur_burl, app_slug, req_role, per_page=20):
        from flask import render_template, abort, request
        from flask_login import login_required, current_user
        from arasCore.rbac import check_permission
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]

        # Derive doctype key from the model's table name for per-user settings
        _doctype_key = model.__tablename__ if hasattr(model, "__tablename__") else tname

        @login_required
        def view():
            if req_role and not current_user.has_role(req_role):
                abort(403)
            if not check_permission(current_user, app_slug, tname, "view"):
                abort(403)

            # Load per-user list view setting (per_page, view_mode, show_totals)
            effective_per_page = per_page
            view_mode = "list"
            show_totals = False
            user_setting = None
            try:
                from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
                user_setting = ErpListViewSetting.query.filter_by(
                    user_id=current_user.id, doctype=_doctype_key
                ).first()
                if user_setting:
                    if user_setting.page_size and user_setting.page_size > 0:
                        effective_per_page = user_setting.page_size
                    view_mode = user_setting.view_mode or "list"
                    show_totals = bool(user_setting.show_totals)
            except Exception:
                pass

            # Per-request per_page override (from selector in UI)
            req_per_page = request.args.get("per_page", type=int)
            if req_per_page and req_per_page > 0:
                effective_per_page = req_per_page
                # Persist change to DB
                try:
                    from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
                    if user_setting is None:
                        from arasCore.lib.extensions import db as _db
                        user_setting = ErpListViewSetting(
                            user_id=current_user.id, doctype=_doctype_key,
                            page_size=req_per_page
                        )
                        _db.session.add(user_setting)
                    else:
                        user_setting.page_size = req_per_page
                    from arasCore.lib.extensions import db as _db
                    _db.session.commit()
                except Exception:
                    pass

            # Resolve searchable columns from mgr_column metadata
            search_cols = []
            try:
                from arasCore.arasAdmin.models import AppManagerColumn
                search_cols = [
                    c.name for c in AppManagerColumn.query.filter_by(
                        table_id=table_id, searchable=True
                    ).all()
                ]
            except Exception:
                pass

            q_obj, active_filters, search_q = apply_search_and_filters(
                model.query, model, search_cols, request
            )
            page = request.args.get("page", 1, type=int)
            pagination = q_obj.paginate(page=page, per_page=effective_per_page, error_out=False)

            filter_cols = [(label, field) for label, field in vcols]

            # Build FK display name maps for list view
            rel_maps = {}
            for _, fname in vcols:
                if fname not in model.__table__.c:
                    continue
                col_c = model.__table__.c[fname]
                if not col_c.foreign_keys:
                    continue
                try:
                    fk = list(col_c.foreign_keys)[0]
                    ref_table = fk.column.table
                    ref_model = None
                    for mapper in db.Model.registry.mappers:
                        if mapper.local_table.name == ref_table.name:
                            ref_model = mapper.class_
                            break
                    if ref_model:
                        rows = ref_model.query.all()
                        rel_maps[fname] = {
                            row.id: (
                                getattr(row, "name", None)
                                or getattr(row, "title", None)
                                or getattr(row, "username", None)
                                or str(row.id)
                            )
                            for row in rows
                        }
                except Exception:
                    pass

            # Find linked report for this doctype (for "Report View" switch button)
            linked_report_url = None
            try:
                from aras.app_erp.erp_core.models.report import ErpReport
                rpt = ErpReport.query.filter_by(
                    name=_doctype_key, is_active=True
                ).first()
                if rpt is None:
                    # Try matching by table name patterns (e.g. acc_sales_invoice → sales_summary)
                    name_map = {
                        "acc_sales_invoice":    "sales_summary",
                        "acc_purchase_invoice": "purchase_summary",
                        "pos_order":            "pot_sales_report",
                        "pos_session":          "pos_shift_report",
                    }
                    mapped = name_map.get(_doctype_key)
                    if mapped:
                        rpt = ErpReport.query.filter_by(name=mapped, is_active=True).first()
                if rpt:
                    linked_report_url = f"/admin/erp/reports/{rpt.id}/"
            except Exception:
                pass

            return render_template(
                "admin/aras_list.html",
                title=title, main_title=main_t,
                items=pagination.items, view_columns=vcols,
                pagination=pagination, per_page=effective_per_page,
                rel_maps=rel_maps,
                add_url=f"{adm_burl}/add/",
                edit_url_base=adm_burl,
                delete_url_base=adm_burl,
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
                search_enabled=bool(search_cols),
                search_q=search_q,
                filter_cols=filter_cols,
                active_filters=active_filters,
                view_mode=view_mode,
                show_totals=show_totals,
                linked_report_url=linked_report_url,
                doctype_key=_doctype_key,
            )
        return view

    def make_adm_add(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id, sibling_tabs, cur_burl, app_slug, req_role):
        from flask import render_template, redirect, flash, abort
        from flask_login import login_required, current_user
        from arasCore.rbac import check_permission
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]

        @login_required
        def view():
            if req_role and not current_user.has_role(req_role):
                abort(403)
            if not check_permission(current_user, app_slug, tname, "create"):
                abort(403)
            form = form_cls()
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                obj = model()
                before_hook, after_hook = _invoke_hooks(obj, is_new=True)
                before_hook()
                form.populate_obj(obj)
                db.session.add(obj)
                db.session.commit()
                after_hook()
                flash("Record added.", "success")
                return redirect(f"{adm_burl}/")
            return render_template(
                "admin/aras_admin_form.html",
                title=f"Add — {title}", main_title=main_t,
                form=form, action=f"{adm_burl}/add/", list_url=f"{adm_burl}/",
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
            )
        return view

    def make_adm_edit(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id, sibling_tabs, cur_burl, app_slug, req_role, child_defs=None):
        from flask import render_template, redirect, flash, abort
        from flask_login import login_required, current_user
        from arasCore.rbac import check_permission
        adm_sibling_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]
        _child_defs = child_defs or []

        @login_required
        def view(item_id):
            if req_role and not current_user.has_role(req_role):
                abort(403)
            if not check_permission(current_user, app_slug, tname, "edit"):
                abort(403)
            obj  = model.query.get_or_404(item_id)
            form = form_cls(obj=obj)
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                before_hook, after_hook = _invoke_hooks(obj, is_new=False)
                before_hook()
                form.populate_obj(obj)
                db.session.commit()
                after_hook()
                flash("Record updated.", "success")
                return redirect(f"{adm_burl}/")
            # Build child table data: query each child filtered by parent FK
            child_tables = []
            for cd in _child_defs:
                try:
                    rows = cd["model"].query.filter(
                        getattr(cd["model"], cd["fk_col"]) == item_id
                    ).all()
                    child_tables.append({
                        "title":   cd["title"],
                        "vcols":   cd["vcols"],
                        "adm_url": cd["adm_url"],
                        "fk_col":  cd["fk_col"],
                        "rows":    rows,
                        "parent_id": item_id,
                    })
                except Exception:
                    pass
            return render_template(
                "admin/aras_admin_form.html",
                title=f"Edit — {title}", main_title=main_t,
                form=form, action=f"{adm_burl}/{item_id}/", list_url=f"{adm_burl}/",
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_sibling_tabs, current_tab_url=cur_burl,
                child_tables=child_tables,
            )
        return view

    def make_adm_delete(model, adm_burl, app_slug, req_role):
        from flask import redirect, flash, abort
        from flask_login import login_required, current_user
        from arasCore.rbac import check_permission

        @login_required
        def view(item_id):
            if req_role and not current_user.has_role(req_role):
                abort(403)
            if not check_permission(current_user, app_slug, tname, "delete"):
                abort(403)
            obj = model.query.get_or_404(item_id)
            from arasCore.lib.audit import maybe_log, _snapshot
            maybe_log(obj, action="delete", before=_snapshot(obj))
            db.session.delete(obj)
            db.session.commit()
            flash("Record deleted.", "warning")
            return redirect(f"{adm_burl}/")
        return view

    def make_adm_bulk_delete(model, adm_burl, app_slug, req_role):
        from flask import request, redirect, flash, abort
        from flask_login import login_required, current_user
        from arasCore.rbac import check_permission

        @login_required
        def view():
            if req_role and not current_user.has_role(req_role):
                abort(403)
            if not check_permission(current_user, app_slug, tname, "delete"):
                abort(403)
            raw = request.form.get("ids", "")
            ids = [i.strip() for i in raw.split(",") if i.strip().isdigit()]
            deleted = 0
            for id_str in ids:
                obj = model.query.get(int(id_str))
                if obj:
                    try:
                        from arasCore.lib.audit import maybe_log, _snapshot
                        maybe_log(obj, action="delete", before=_snapshot(obj))
                        db.session.delete(obj)
                        deleted += 1
                    except Exception:
                        pass
            try:
                db.session.commit()
                flash(f"{deleted} record(s) deleted.", "warning")
            except Exception as ex:
                db.session.rollback()
                flash(str(ex), "danger")
            return redirect(f"{adm_burl}/")
        return view

    # Web view helpers (public read, login_required for write, web templates)

    def make_web_list(model, title, main_t, vcols, burl, app_title, sibling_tabs, cur_burl):
        from flask import render_template

        def view():
            items = model.query.all()
            return render_template(
                "admin/aras_list.html",
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
                before_hook, after_hook = _invoke_hooks(obj, is_new=True)
                before_hook()
                form.populate_obj(obj)
                db.session.add(obj)
                db.session.commit()
                after_hook()
                flash("Record added.", "success")
                return redirect(f"{burl}/")
            return render_template(
                "admin/aras_admin_form.html",
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
                before_hook, after_hook = _invoke_hooks(obj, is_new=False)
                before_hook()
                form.populate_obj(obj)
                db.session.commit()
                after_hook()
                flash("Record updated.", "success")
                return redirect(f"{burl}/")
            return render_template(
                "admin/aras_admin_form.html",
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
            from arasCore.lib.audit import maybe_log, _snapshot
            maybe_log(obj, action="delete", before=_snapshot(obj))
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
    bp.add_url_rule(f"{adm_url}/",               endpoint=f"{ep}_adm_index",       view_func=make_adm_list(model, title, main_t, vcols, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role, per_page=snap.get("per_page", 20)))
    bp.add_url_rule(f"{adm_url}/add/",           endpoint=f"{ep}_adm_add",         view_func=make_adm_add(model, form_cls, title, main_t, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role),  methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/", endpoint=f"{ep}_adm_edit",        view_func=make_adm_edit(model, form_cls, title, main_t, adm_url, app_title, app_id, table_id, sibling_tabs, adm_url, app_slug, req_role, child_defs=child_defs), methods=["GET","POST"])
    bp.add_url_rule(f"{adm_url}/<int:item_id>/delete/", endpoint=f"{ep}_adm_delete", view_func=make_adm_delete(model, adm_url, app_slug, req_role), methods=["POST"])
    bp.add_url_rule(f"{adm_url}/bulk-delete/",   endpoint=f"{ep}_adm_bulk_delete", view_func=make_adm_bulk_delete(model, adm_url, app_slug, req_role), methods=["POST"])

    # Register ke universal API — handler ada di api_handler.py, bukan di sini
    try:
        from arasCore.lib.api_handler import register_api_model
        register_api_model(burl.strip("/"), model)
    except Exception as _e:
        logger.warning(f"[services] api_handler register skipped: {_e}")


def _detect_parent_fk(child_model, parent_model):
    """Return the FK column name on child_model that references parent_model's table."""
    try:
        parent_table = parent_model.__tablename__
        for col in child_model.__table__.columns:
            for fk in col.foreign_keys:
                if fk.column.table.name == parent_table:
                    return col.name
    except Exception:
        pass
    return None


def _get_child_tables_for_model(model):
    """
    For code-based (manifest) models: find one-to-many relationships via SA inspect.
    Returns list of {title, model, vcols, adm_url, fk_col} dicts.
    Used when all_snaps is not available (blueprints.py path).
    """
    from sqlalchemy import inspect as sa_inspect
    result = []
    try:
        mapper = sa_inspect(model)
        for rel in mapper.relationships:
            if rel.uselist:  # one-to-many
                child_cls = rel.mapper.class_
                fk_col = _detect_parent_fk(child_cls, model)
                if not fk_col:
                    continue
                child_title = child_cls.__tablename__.replace("_", " ").title()
                vcols = [(c.name, c.name) for c in child_cls.__table__.columns if c.name not in ("id",)][:5]
                result.append({
                    "title":   child_title,
                    "model":   child_cls,
                    "vcols":   vcols,
                    "adm_url": None,
                    "fk_col":  fk_col,
                })
    except Exception:
        pass
    return result


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
    """Load all active AppManagerApp records and register them as blueprints.

    Skips apps that are already handled by a Python manifest (AppHelper) —
    those are registered by blueprints._register_helper() and do not need
    dynamic model/route generation from mgr_table/mgr_column.
    """
    try:
        from arasCore.arasAdmin.models import AppManagerApp
        from arasCore.lib.blueprints import get_helper_registry
        with flask_app.app_context():
            db.create_all()
            apps = AppManagerApp.query.filter_by(is_active=True).all()
            app_ids = [(a.id, a.name) for a in apps]
            logger.info(f"[services] Found {len(app_ids)} active built app(s).")

        helper_registry = get_helper_registry()
        for app_id, app_name in app_ids:
            if app_name in helper_registry:
                logger.info(f"[services] skip '{app_name}' — already handled by Python manifest")
                continue
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
