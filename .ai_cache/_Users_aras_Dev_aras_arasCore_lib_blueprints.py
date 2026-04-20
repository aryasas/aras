import os
import logging
from importlib import import_module

from flask import Blueprint
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

    api_prefix = helper.get_api_prefix()    # /api/soc
    adm_prefix = helper.get_admin_prefix()  # /admin/soc

    # ── 1. Resource CRUD → daftar ke universal API registry ──────────────────
    for res in helper.resources:
        url_key = f"{helper.name}/{res.name}"
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
        ep_name  = f"api_{helper.name}_{rel_path.replace('/', '_')}"

        handler = login_required(cr.handler) if cr.require_auth else cr.handler

        try:
            helper_bp.add_url_rule(full_url, endpoint=ep_name, view_func=handler, methods=cr.methods)
            register_custom_route(f"{helper.name}/{rel_path}", cr.handler, methods=cr.methods, require_auth=cr.require_auth)
            logger.debug(f"[blueprints] custom API: {full_url}")
        except Exception as e:
            logger.error(f"[blueprints] gagal mount custom route {full_url}: {e}")

    flask_app.register_blueprint(helper_bp)
    _helper_registry[helper.name] = helper
    logger.debug(f"[blueprints] helper registered: {helper.name}")


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
        BaseModelForm = model_form_factory(FlaskForm)
        _m = _model
        _skip = {"created_at", "updated_at", "created_by_id", "updated_by_id"}
        # only include columns that are not PKs, not FKs, not in skip list, not auto-datetime
        _only = [
            c.name for c in _m.__table__.columns
            if c.name not in _skip
            and not c.primary_key
            and not c.foreign_keys
            and not (isinstance(c.type, (_sa.DateTime, _sa.Date)) and c.default is not None)
        ]

        class ModelForm(BaseModelForm):
            @classmethod
            def get_session(cls):
                return db.session
            class Meta:
                model = _m
                only = _only if _only else None
        return ModelForm

    def make_list(model=model, res_name=res_name, base_url=base_url, app_title=app_title, res=res, res_title=res_title):
        @login_required
        def view():
            items = model.query.order_by(model.id.desc()).all()
            cols = res.list_columns or [
                (c.name.replace("_", " ").title(), c.name)
                for c in model.__table__.columns
                if c.name not in ("id", "created_by_id", "updated_by_id")
            ][:6]
            return render_template(
                "admin/ab_list.html",
                title=res_title,
                main_title=res_title,
                items=items,
                data_list=items,
                view_columns=cols,
                add_url=f"{base_url}/add/",
                edit_url_base=base_url,
                delete_url_base=base_url,
            )
        return view

    def make_add(model=model, base_url=base_url, app_title=app_title, res_title=res_title):
        @login_required
        def view():
            form = _make_form(model)()
            if form.validate_on_submit():
                try:
                    obj = model()
                    form.populate_obj(obj)
                    db.session.add(obj)
                    db.session.commit()
                    flash("Record created.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    flash(str(ex), "danger")
            return render_template(
                "admin/ab_form.html",
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
            obj = model.query.get_or_404(item_id)
            form = _make_form(model)(obj=obj)
            if form.validate_on_submit():
                try:
                    form.populate_obj(obj)
                    db.session.commit()
                    flash("Record updated.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    flash(str(ex), "danger")
            return render_template(
                "admin/ab_form.html",
                title=f"Edit {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/{item_id}/edit/",
                list_url=f"{base_url}/",
            )
        return view

    def make_delete(model=model, base_url=base_url):
        @login_required
        def view(item_id):
            obj = model.query.get_or_404(item_id)
            try:
                db.session.delete(obj)
                db.session.commit()
                flash("Record deleted.", "warning")
            except Exception as ex:
                db.session.rollback()
                flash(str(ex), "danger")
            return redirect(f"{base_url}/")
        return view

    # Endpoint name: sanitize slash → underscore
    ep = f"adm_{helper.name}_{res_name.replace('/', '_')}"
    try:
        bp.add_url_rule(f"{base_url}/",                      endpoint=f"{ep}_list",   view_func=make_list())
        bp.add_url_rule(f"{base_url}/add/",                  endpoint=f"{ep}_add",    view_func=make_add(),  methods=["GET", "POST"])
        bp.add_url_rule(f"{base_url}/<int:item_id>/edit/",   endpoint=f"{ep}_edit",   view_func=make_edit(), methods=["GET", "POST"])
        bp.add_url_rule(f"{base_url}/<int:item_id>/delete/", endpoint=f"{ep}_delete", view_func=make_delete(), methods=["POST"])
    except Exception as e:
        logger.error(f"[blueprints] gagal mount admin resource {base_url}: {e}")


def _register_aras_apps(app):
    """
    Auto-discover dan register app_* dari folder aras/.
    Setiap app harus expose app_bp di views.py atau views/__init__.py.
    Jika ada manifest.py dengan AppHelper, framework baca dan proses.
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
        if not has_views:
            logger.debug(f"[blueprints] skip {entry} — no views.py")
            continue

        pkg_name = f"aras.{entry}"
        try:
            mod = import_module(f"{pkg_name}.views")
            bp  = getattr(mod, "app_bp", None) or getattr(mod, "bp", None)
            if bp is None:
                logger.warning(f"[blueprints] {pkg_name}.views has no app_bp — skip")
                continue

            app.register_blueprint(bp)

            # Baca manifest — di-register ke app langsung (bukan ke bp)
            helper = _load_manifest(pkg_name)
            if helper:
                _register_helper(app, helper)
                logger.info(
                    f"[blueprints] registered: {entry} + manifest "
                    f"({len(helper.resources)} resources, {len(helper.custom_routes)} custom routes)"
                )
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
