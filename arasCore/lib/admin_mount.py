"""
arasCore/lib/admin_mount.py — AdminResourceMounter

Extracted from blueprints._mount_admin_resource to eliminate nested closures
and make each CRUD action a discrete, testable method.
"""
import logging

from flask import render_template, redirect, flash, abort
from flask_login import login_required

logger = logging.getLogger(__name__)


def _col_label(name: str) -> str:
    s = name[:-3] if name.endswith("_id") else name
    return s.replace("_", " ").title()


def _build_model_form(model):
    """Build a WTForms form class from a SQLAlchemy model."""
    import sqlalchemy as _sa
    from flask_wtf import FlaskForm
    from wtforms import SelectField
    from wtforms.validators import Optional as _Opt
    from wtforms_alchemy import model_form_factory
    from arasCore.lib.extensions import db

    BaseModelForm = model_form_factory(FlaskForm)
    _skip = {"created_at", "updated_at", "created_by_id", "updated_by_id"}
    _only = [
        c.name for c in model.__table__.columns
        if c.name not in _skip
        and not c.primary_key
        and not c.foreign_keys
        and not (isinstance(c.type, (_sa.DateTime, _sa.Date)) and c.default is not None)
    ]
    _fk_cols = [
        c for c in model.__table__.columns
        if c.foreign_keys and c.name not in _skip and not c.primary_key
    ]
    fk_fields = {}
    for col in _fk_cols:
        lbl = col.name[:-3].replace("_", " ").title() if col.name.endswith("_id") else col.name.replace("_", " ").title()
        fk_fields[col.name] = SelectField(
            lbl,
            coerce=lambda x: int(x) if x and str(x) != "0" else None,
            choices=[(0, "— Select —")],
            validators=[_Opt()],
        )

    class_attrs = {"get_session": classmethod(lambda cls: db.session)}
    class_attrs.update(fk_fields)
    class_attrs["Meta"] = type("Meta", (), {"model": model, "only": _only if _only else None})
    return type(f"ModelForm_{model.__tablename__}", (BaseModelForm,), class_attrs)


def _resolve_search_cols(helper, res, model):
    """Get searchable column names for a resource."""
    search_cols = []
    try:
        from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable, AppManagerColumn
        app_rec = AppManagerApp.query.filter_by(url=getattr(helper, "admin_slug", helper.name)).first()
        if app_rec:
            tbl_rec = AppManagerTable.query.filter_by(
                app_id=app_rec.id, db_table_name=model.__tablename__
            ).first()
            if tbl_rec:
                search_cols = [
                    c.name for c in AppManagerColumn.query.filter_by(
                        table_id=tbl_rec.id, searchable=True
                    ).all()
                ]
    except Exception:
        pass
    return search_cols


def _build_fk_maps(cols, model):
    """Build FK → display name maps for list view columns."""
    from arasCore.lib.extensions import db
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
    return rel_maps


class AdminResourceMounter:
    """Mounts CRUD admin routes for one ResourceDef onto a Blueprint."""

    def __init__(self, bp, res, adm_prefix, helper):
        self.bp        = bp
        self.res       = res
        self.helper    = helper
        self.model     = res.model
        self.base_url  = f"{adm_prefix}/{res.name}"
        self.app_title = helper.title
        self.res_title = res.name.replace("/", " › ").replace("_", " ").title()

    def _rbac(self, action):
        from arasCore.rbac import check_permission
        from flask_login import current_user
        return check_permission(current_user, self.helper.name, self.res.name, action)

    def _resolve_app_table_ids(self):
        try:
            from arasCore.arasAdmin.models import AppManagerApp, AppManagerTable
            app_rec = AppManagerApp.query.filter_by(url=getattr(self.helper, "admin_slug", self.helper.name)).first()
            if app_rec:
                tbl_rec = AppManagerTable.query.filter_by(
                    app_id=app_rec.id, db_table_name=self.model.__tablename__
                ).first()
                return app_rec.id, tbl_rec.id if tbl_rec else None
        except Exception:
            pass
        return None, None

    def make_list(self):
        model     = self.model
        base_url  = self.base_url
        res_title = self.res_title
        helper    = self.helper
        res       = self.res

        @login_required
        def view():
            from flask import request as _req
            if not self._rbac("view"):
                abort(403)

            cols = res.list_columns or [
                (_col_label(c.name), c.name)
                for c in model.__table__.columns
                if c.name not in ("id", "created_by_id", "updated_by_id", "created_at", "updated_at", "deleted_at")
            ][:6]

            _app_id, _table_id = self._resolve_app_table_ids()
            search_cols = _resolve_search_cols(helper, res, model)
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
            rel_maps = _build_fk_maps(cols, model)

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

    def make_add(self):
        from arasCore.lib.extensions import db
        model         = self.model
        base_url      = self.base_url
        app_title     = self.app_title
        res_title     = self.res_title
        show_save_btn = getattr(self.res, "show_save_btn", True)

        @login_required
        def view():
            if not self._rbac("create"):
                abort(403)
            form = _build_model_form(model)()
            from arasCore.arasAdmin.services import _populate_relation_choices, _invoke_hooks
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                try:
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
                show_save_btn=show_save_btn,
            )
        return view

    def make_edit(self):
        from arasCore.lib.extensions import db
        model         = self.model
        base_url      = self.base_url
        app_title     = self.app_title
        res_title     = self.res_title
        show_save_btn = getattr(self.res, "show_save_btn", True)

        @login_required
        def view(item_id):
            if not self._rbac("edit"):
                abort(403)
            obj  = model.query.get_or_404(item_id)
            form = _build_model_form(model)(obj=obj)
            from arasCore.arasAdmin.services import _populate_relation_choices, _invoke_hooks, _get_child_tables_for_model
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                try:
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
                action=f"{base_url}/{item_id}/",
                list_url=f"{base_url}/",
                child_tables=child_tables,
                show_save_btn=show_save_btn,
            )
        return view

    def make_delete(self):
        from arasCore.lib.extensions import db
        model    = self.model
        base_url = self.base_url

        @login_required
        def view(item_id):
            if not self._rbac("delete"):
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

    def make_bulk_delete(self):
        from arasCore.lib.extensions import db
        from flask import request
        model    = self.model
        base_url = self.base_url

        @login_required
        def view():
            if not self._rbac("delete"):
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

    def mount(self):
        """Register all CRUD routes onto the blueprint."""
        ep  = f"adm_{self.helper.name}_{self.res.name.replace('/', '_')}"
        url = self.base_url
        try:
            self.bp.add_url_rule(f"{url}/",                      endpoint=f"{ep}_list",        view_func=self.make_list())
            self.bp.add_url_rule(f"{url}/add/",                  endpoint=f"{ep}_add",         view_func=self.make_add(),         methods=["GET", "POST"])
            self.bp.add_url_rule(f"{url}/<int:item_id>/",        endpoint=f"{ep}_edit",        view_func=self.make_edit(),        methods=["GET", "POST"])
            self.bp.add_url_rule(f"{url}/<int:item_id>/delete/", endpoint=f"{ep}_delete",      view_func=self.make_delete(),      methods=["POST"])
            self.bp.add_url_rule(f"{url}/bulk-delete/",          endpoint=f"{ep}_bulk_delete", view_func=self.make_bulk_delete(), methods=["POST"])
        except Exception as ex:
            logger.error(f"[admin_mount] failed to mount {url}: {ex}")
