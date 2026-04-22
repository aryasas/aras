import os
import re
import logging
from importlib import import_module

from flask import Blueprint, abort
from flask_login import login_required

logger = logging.getLogger(__name__)

_SKIP = {"app_admin", "app_manager"}

# Registry semua AppHelper dari code-based apps — dibaca oleh build_sidebar_menu()
_helper_registry: dict = {}   # {app_name: AppHelper}


def get_helper_registry() -> dict:
    return dict(_helper_registry)


def _load_manifest(pkg_name: str):
    """
    Coba import {pkg_name}.manifest dan kembalikan AppHelper instance.
    Kembalikan None jika tidak ada atau bukan AppHelper.
    """
    from arasCore.lib.app_helper import AppHelper
    try:
        mod = import_module(f"{pkg_name}.manifest")
        helper = getattr(mod, "helper", None)
        if isinstance(helper, AppHelper):
            return helper
        logger.debug(f"[blueprints] {pkg_name}/manifest.py: tidak punya 'helper' AppHelper")
    except ModuleNotFoundError:
        pass
    except Exception as e:
        logger.warning(f"[blueprints] gagal load manifest {pkg_name}: {e}")
    return None


def _register_helper(flask_app, helper):
    """
    Baca AppHelper dan mount semua routes langsung ke flask_app (bukan blueprint)
    agar URL tidak kena prefix dari blueprint app.

    Routes yang dibuat:
      /api/<app>/<resource>/            — universal CRUD via api_handler
      /api/<app>/<custom_path>/         — custom handlers dari app
      /admin/<app>/<resource>/          — admin list + delete
    """
    from arasCore.lib.api_handler import register_api_model, register_custom_route

    # Buat satu blueprint khusus untuk helper ini (tanpa url_prefix)
    # agar endpoint name tetap unik tanpa konflik dengan blueprint app
    helper_bp = Blueprint(f"_helper_{helper.name}", __name__)

    api_prefix = helper.get_api_prefix()    # /api/<api_slug>
    adm_prefix = helper.get_admin_prefix()  # /admin/<admin_slug>

    # ── 1. Resource CRUD → daftar ke universal API registry ──────────────────
    for res in helper.resources:
        if res.model is None:
            continue  # link-only ResourceDef (custom url, no CRUD)
        url_key = f"{helper.api_slug}/{res.name}"
        register_api_model(
            url_key,
            res.model,
            serializer=res.get_serializer(),
            readonly=res.readonly,
            handler=res.handler,
        )
        logger.debug(f"[blueprints] API resource: /api/{url_key}/")

        if res.admin_list:
            _mount_admin_resource(helper_bp, res, adm_prefix, helper)

    # ── 2. Custom routes → /api/<app>/<path>/ ────────────────────────────────
    for cr in helper.custom_routes:
        rel_path = cr.path.strip("/")
        full_url = f"{api_prefix}/{rel_path}/"
        clean    = re.sub(r"<[^>]+>", "x", rel_path).replace("/", "_")
        ep_name  = f"api_{helper.api_slug}_{clean}"

        handler = login_required(cr.handler) if cr.require_auth else cr.handler

        try:
            helper_bp.add_url_rule(full_url, endpoint=ep_name, view_func=handler, methods=cr.methods)
            register_custom_route(f"{helper.api_slug}/{rel_path}", cr.handler, methods=cr.methods, require_auth=cr.require_auth)
            logger.debug(f"[blueprints] custom API: {full_url}")
        except Exception as e:
            logger.error(f"[blueprints] gagal mount custom route {full_url}: {e}")

    # ── 3. Auto-mount /admin/<admin_slug>/settings/ ────────────────────────────
    try:
        from arasCore.arasAdmin.settings_service import mount_settings_route
        mount_settings_route(
            helper_bp, helper.admin_slug, helper.title,
            schema=getattr(helper, "settings_schema", None) or [],
            is_dynamic=False,
            endpoint=f"settings_{helper.name}",
            registry_key=helper.name,
        )
    except Exception as e:
        logger.warning(f"[blueprints] settings mount failed for {helper.name}: {e}")

    # ── 4. Auto-mount /admin/<admin_slug>/ home page ───────────────────────────
    try:
        from arasCore.arasAdmin.home_service import mount_home_route
        mount_home_route(
            helper_bp, helper.admin_slug, helper.title,
            is_dynamic=False,
            endpoint=f"home_{helper.name}",
            registry_key=helper.name,
        )
    except Exception as e:
        logger.warning(f"[blueprints] home mount failed for {helper.name}: {e}")

    # ── 5. Auto-mount /admin/<admin_slug>/<slug>/ for MenuGroup sub-pages ──────
    if helper.menu_groups:
        try:
            from arasCore.arasAdmin.home_service import mount_group_route
            mount_group_route(
                helper_bp, helper.admin_slug, helper.title,
                endpoint=f"group_{helper.name}",
                registry_key=helper.name,
            )
        except Exception as e:
            logger.warning(f"[blueprints] group mount failed for {helper.name}: {e}")

    @helper_bp.before_request
    def _set_gmenu():
        from flask import g, request as _req
        from flask_login import current_user
        if current_user.is_authenticated and not hasattr(g, "gmenu"):
            from arasCore.arasAdmin.services import build_sidebar_menu
            g.gmenu = build_sidebar_menu()
        # Expose app template for non-admin routes so handlers can render custom layouts
        if not _req.path.startswith("/admin/"):
            g.app_template = getattr(helper, "template", None)

    flask_app.register_blueprint(helper_bp)
    _helper_registry[helper.name] = helper
    logger.debug(f"[blueprints] helper registered: {helper.name}")


def _rbac_check(helper, res, action):
    """Return True if current_user may perform action on resource. Always True when RBAC disabled."""
    from arasCore.rbac import check_permission
    from flask_login import current_user
    return check_permission(current_user, helper.name, res.name, action)


def _mount_admin_resource(bp, res, adm_prefix, helper):
    """
    Buat admin list + add + edit + delete route untuk satu ResourceDef.
    Di-mount ke blueprint tanpa prefix — URL sudah absolute.
    """
    from arasCore.lib.extensions import db
    from flask import render_template, redirect, flash, request
    from wtforms_alchemy import model_form_factory
    from flask_wtf import FlaskForm

    model     = res.model
    res_name  = res.name
    base_url  = f"{adm_prefix}/{res_name}"
    app_title = helper.title
    res_title = res_name.replace("/", " › ").replace("_", " ").title()

    def _make_form(_model=model):
        import sqlalchemy as _sa
        from wtforms import SelectField
        from wtforms.validators import Optional as _Opt
        BaseModelForm = model_form_factory(FlaskForm)
        _m = _model
        _skip = {"created_at", "updated_at", "created_by_id", "updated_by_id"}
        _only = [
            c.name for c in _m.__table__.columns
            if c.name not in _skip
            and not c.primary_key
            and not c.foreign_keys
            and not (isinstance(c.type, (_sa.DateTime, _sa.Date)) and c.default is not None)
        ]
        # FK columns become SelectFields (populated at request time by _populate_relation_choices)
        _fk_cols = [
            c for c in _m.__table__.columns
            if c.foreign_keys and c.name not in _skip and not c.primary_key
        ]
        _fk_field_defs = {}
        for _c in _fk_cols:
            _lbl = _c.name[:-3].replace("_", " ").title() if _c.name.endswith("_id") else _c.name.replace("_", " ").title()
            _fk_field_defs[_c.name] = SelectField(
                _lbl,
                coerce=lambda x: int(x) if x and str(x) != "0" else None,
                choices=[(0, "— Select —")],
                validators=[_Opt()],
            )

        # Build class attrs including FK SelectFields so metaclass picks them up
        class_attrs = {"get_session": classmethod(lambda cls: db.session)}
        class_attrs.update(_fk_field_defs)
        class_attrs["Meta"] = type("Meta", (), {"model": _m, "only": _only if _only else None})

        ModelForm = type(
            f"ModelForm_{_m.__tablename__}",
            (BaseModelForm,),
            class_attrs,
        )
        return ModelForm

    def make_list(model=model, res_name=res_name, base_url=base_url, app_title=app_title, res=res, res_title=res_title):
        @login_required
        def view():
            from flask import request as _req
            if not _rbac_check(helper, res, "view"):
                abort(403)

            def _col_label(n):
                s = n[:-3] if n.endswith("_id") else n
                return s.replace("_", " ").title()

            cols = res.list_columns or [
                (_col_label(c.name), c.name)
                for c in model.__table__.columns
                if c.name not in ("id", "created_by_id", "updated_by_id", "created_at", "updated_at", "deleted_at")
            ][:6]

            # Resolve mgr_app/mgr_table IDs so the Customize button appears
            _app_id = _table_id = None
            search_cols = []
            try:
                from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable, AppManagerColumn
                _app_rec = AppManagerApp.query.filter_by(name=helper.name).first()
                if _app_rec:
                    _app_id = _app_rec.id
                    _tbl_rec = AppManagerTable.query.filter_by(
                        app_id=_app_rec.id, db_table_name=model.__tablename__
                    ).first()
                    if _tbl_rec:
                        _table_id = _tbl_rec.id
                        search_cols = [
                            c.name for c in AppManagerColumn.query.filter_by(
                                table_id=_tbl_rec.id, searchable=True
                            ).all()
                        ]
            except Exception:
                pass

            # Fall back: use string-type view_columns as search targets if none configured
            if not search_cols:
                search_cols = [
                    fname for _, fname in cols
                    if fname in model.__table__.c
                    and hasattr(model.__table__.c[fname].type, "length")
                ][:3]

            from arasCore.arasAdmin.services import apply_search_and_filters
            q_obj, active_filters, search_q = apply_search_and_filters(
                model.query.order_by(model.id.desc()), model, search_cols, _req
            )
            items = q_obj.all()

            # Build FK display name maps for columns shown in list
            rel_maps = {}
            for _, fname in cols:
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

            return render_template(
                "admin/aras_list.html",
                title=res_title,
                main_title=res_title,
                items=items,
                view_columns=cols,
                rel_maps=rel_maps,
                add_url=f"{base_url}/add/",
                edit_url_base=base_url,
                delete_url_base=base_url,
                app_id=_app_id,
                table_id=_table_id,
                search_enabled=True,
                search_q=search_q,
                filter_cols=cols,
                active_filters=active_filters,
            )
        return view

    def make_add(model=model, base_url=base_url, app_title=app_title, res_title=res_title):
        @login_required
        def view():
            if not _rbac_check(helper, res, "create"):
                abort(403)
            form = _make_form(model)()
            from arasCore.arasAdmin.services import _populate_relation_choices
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                try:
                    from arasCore.arasAdmin.services import _invoke_hooks
                    obj = model()
                    before_hook, after_hook = _invoke_hooks(obj, is_new=True)
                    before_hook()
                    form.populate_obj(obj)
                    db.session.add(obj)
                    db.session.commit()
                    after_hook()
                    flash("Record created.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    flash(str(ex), "danger")
            return render_template(
                "admin/aras_admin_form.html",
                title=f"Add {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/add/",
                list_url=f"{base_url}/",
            )
        return view

    def make_edit(model=model, base_url=base_url, app_title=app_title, res_title=res_title):
        @login_required
        def view(item_id):
            if not _rbac_check(helper, res, "edit"):
                abort(403)
            obj = model.query.get_or_404(item_id)
            form = _make_form(model)(obj=obj)
            from arasCore.arasAdmin.services import _populate_relation_choices
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                try:
                    from arasCore.arasAdmin.services import _invoke_hooks
                    before_hook, after_hook = _invoke_hooks(obj, is_new=False)
                    before_hook()
                    form.populate_obj(obj)
                    db.session.commit()
                    after_hook()
                    flash("Record updated.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    flash(str(ex), "danger")
            # Detect child tables via SA relationships
            from arasCore.arasAdmin.services import _get_child_tables_for_model
            child_tables = []
            for cd in _get_child_tables_for_model(model):
                try:
                    rows = cd["model"].query.filter(
                        getattr(cd["model"], cd["fk_col"]) == item_id
                    ).all()
                    child_tables.append({
                        "title":     cd["title"],
                        "vcols":     cd["vcols"],
                        "adm_url":   cd["adm_url"],
                        "fk_col":    cd["fk_col"],
                        "rows":      rows,
                        "parent_id": item_id,
                    })
                except Exception:
                    pass
            return render_template(
                "admin/aras_admin_form.html",
                title=f"Edit {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/{item_id}/edit/",
                list_url=f"{base_url}/",
                child_tables=child_tables,
            )
        return view

    def make_delete(model=model, base_url=base_url):
        @login_required
        def view(item_id):
            if not _rbac_check(helper, res, "delete"):
                abort(403)
            obj = model.query.get_or_404(item_id)
            try:
                from arasCore.lib.audit import maybe_log, _snapshot
                maybe_log(obj, action="delete", before=_snapshot(obj))
                db.session.delete(obj)
                db.session.commit()
                flash("Record deleted.", "warning")
            except Exception as ex:
                db.session.rollback()
                flash(str(ex), "danger")
            return redirect(f"{base_url}/")
        return view

    def make_bulk_delete(model=model, base_url=base_url):
        from flask import request
        @login_required
        def view():
            if not _rbac_check(helper, res, "delete"):
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
            return redirect(f"{base_url}/")
        return view

    # Endpoint name: sanitize slash → underscore
    ep = f"adm_{helper.name}_{res_name.replace('/', '_')}"
    try:
        bp.add_url_rule(f"{base_url}/",                      endpoint=f"{ep}_list",        view_func=make_list())
        bp.add_url_rule(f"{base_url}/add/",                  endpoint=f"{ep}_add",         view_func=make_add(),         methods=["GET", "POST"])
        bp.add_url_rule(f"{base_url}/<int:item_id>/edit/",   endpoint=f"{ep}_edit",        view_func=make_edit(),        methods=["GET", "POST"])
        bp.add_url_rule(f"{base_url}/<int:item_id>/delete/", endpoint=f"{ep}_delete",      view_func=make_delete(),      methods=["POST"])
        bp.add_url_rule(f"{base_url}/bulk-delete/",          endpoint=f"{ep}_bulk_delete", view_func=make_bulk_delete(), methods=["POST"])
    except Exception as e:
        logger.error(f"[blueprints] gagal mount admin resource {base_url}: {e}")


def _is_app_enabled(entry: str, aras_pkg: str) -> bool:
    """
    Return True if the app_* package should be loaded.

    Rules (in order):
    1. Package __init__.py sets ARAS_AUTOLOAD = True  → always load (dev/built-in).
    2. AppManagerApp record exists with is_active=True → load (framework-installed).
    3. Otherwise → skip (app exists on disk but not installed/activated).
    """
    # Rule 1: opt-in autoload flag in __init__.py
    init_path = os.path.join(aras_pkg, entry, "__init__.py")
    if os.path.isfile(init_path):
        try:
            with open(init_path) as fh:
                for line in fh:
                    if line.strip().startswith("ARAS_AUTOLOAD"):
                        if "True" in line:
                            return True
                        break  # found the var but it's False/other
        except Exception:
            pass

    # Rule 2: check DB — only possible after configure_database() ran
    app_name = entry[len("app_"):]  # strip "app_" prefix → "soc", "erp", etc.
    try:
        from arasCore.arasAdmin.models import AppManagerApp
        rec = AppManagerApp.query.filter_by(name=app_name, is_active=True).first()
        if rec:
            return True
    except Exception:
        # DB not ready yet (first boot before create_all) — skip DB check
        pass

    return False


def _register_aras_apps(app):
    """
    Auto-discover dan register app_* dari folder aras/.
    Hanya load app yang memenuhi syarat:
      - ARAS_AUTOLOAD = True di __init__.py, ATAU
      - Ada record AppManagerApp dengan is_active=True di DB.
    """
    aras_pkg = os.path.normpath(os.path.join(app.root_path, "..", "aras"))

    if not os.path.isdir(aras_pkg):
        logger.warning(f"[blueprints] aras package not found at: {aras_pkg}")
        return

    for entry in sorted(os.listdir(aras_pkg)):
        if not entry.startswith("app_") or entry in _SKIP:
            continue

        has_views = (
            os.path.isfile(os.path.join(aras_pkg, entry, "views.py")) or
            os.path.isfile(os.path.join(aras_pkg, entry, "views", "__init__.py"))
        )
        has_manifest = os.path.isfile(os.path.join(aras_pkg, entry, "manifest.py"))
        if not has_views and not has_manifest:
            logger.debug(f"[blueprints] skip {entry} — no views.py or manifest.py")
            continue

        if not _is_app_enabled(entry, aras_pkg):
            logger.info(f"[blueprints] skip {entry} — not installed/active in DB (set ARAS_AUTOLOAD=True to override)")
            continue

        pkg_name = f"aras.{entry}"
        try:
            bp = None
            if has_views:
                mod = import_module(f"{pkg_name}.views")
                bp  = getattr(mod, "app_bp", None) or getattr(mod, "bp", None)
                if bp is not None:
                    app.register_blueprint(bp)

            helper = _load_manifest(pkg_name)
            if helper:
                _register_helper(app, helper)
                logger.info(
                    f"[blueprints] registered: {entry} + manifest "
                    f"({len(helper.resources)} resources, {len(helper.custom_routes)} custom routes)"
                )
            elif bp is None:
                logger.warning(f"[blueprints] {pkg_name} has no app_bp and no manifest — skip")
            else:
                logger.info(f"[blueprints] registered: {entry} (no manifest)")

        except Exception as e:
            logger.error(f"[blueprints] failed to load {entry}: {e}", exc_info=True)


def register_app_modules(app):
    """
    Dipanggil dari arasCore.create_app() setelah auth_bp terdaftar.
    Load app_* dari aras/ lalu register arasAdmin terakhir.
    """
    _register_aras_apps(app)

    from arasCore.arasAdmin import arasAdmin_bp
    app.register_blueprint(arasAdmin_bp)
