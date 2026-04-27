"""
arasCore/lib/admin_mount.py — AdminResourceMounter

Extracted from blueprints._mount_admin_resource to eliminate nested closures
and make each CRUD action a discrete, testable method.
"""
import logging

from flask import render_template, redirect, flash, abort
from flask_login import login_required

logger = logging.getLogger(__name__)


from arasCore.lib.label_utils import humanize, row_display, find_ref_model as _find_ref_model


def _fk_coerce(x):
    try:
        v = int(x)
        return v if v != 0 else None
    except (TypeError, ValueError):
        return None


def _fk_choices(col):
    """Resolve FK choices from the referenced table at request time."""
    try:
        fk = list(col.foreign_keys)[0]
        ref_tname = fk.column.table.name
        ref_model = _find_ref_model(ref_tname)
        if ref_model:
            rows = ref_model.query.order_by(ref_model.id).all()
            return [(0, "— Select —")] + [(r.id, row_display(r)) for r in rows]
    except Exception as _e:
        logger.warning(f"[admin_mount] _fk_choices failed for {col}: {_e}")
    return [(0, "— Select —")]


def _build_model_form(model, obj=None):
    """Build a WTForms form from model.form_columns() with FK choices pre-loaded."""
    import sqlalchemy as _sa
    from wtforms import StringField, TextAreaField, IntegerField, BooleanField, DateField, SelectField
    from wtforms.validators import Optional as _Opt, DataRequired
    from arasCore.lib.forms import _CORE_SYSTEM_INTERNAL
    
    attrs = {}
    for lbl, col_name, col in model.form_columns():
        # Check if the column has a show_in_form attribute (e.g. from mgr_column)
        show_in_form = getattr(col, "show_in_form", True)
        
        # Guard: skip hidden fields or internal system fields
        if not show_in_form or col_name in _CORE_SYSTEM_INTERNAL:
            continue

        req = not col.nullable and col.default is None and not col.server_default
        v = [DataRequired()] if req else [_Opt()]

        if col.foreign_keys:
            # Resolve choices now (inside request) so SelectField data matches on init
            choices = _fk_choices(col)
            attrs[col_name] = SelectField(lbl, coerce=_fk_coerce,
                                          choices=choices, validators=[_Opt()])
        elif isinstance(col.type, _sa.Boolean):
            attrs[col_name] = BooleanField(lbl)
        elif isinstance(col.type, (_sa.Integer, _sa.BigInteger, _sa.SmallInteger)):
            attrs[col_name] = IntegerField(lbl, validators=v)
        elif isinstance(col.type, (_sa.Numeric, _sa.Float)):
            from wtforms import DecimalField
            attrs[col_name] = DecimalField(lbl, validators=v, places=2)
        elif isinstance(col.type, _sa.Text):
            attrs[col_name] = TextAreaField(lbl, validators=v)
        elif isinstance(col.type, _sa.Date):
            attrs[col_name] = DateField(lbl, validators=v)
        elif isinstance(col.type, _sa.DateTime):
            from wtforms.fields import DateTimeLocalField
            attrs[col_name] = DateTimeLocalField(lbl, validators=v)
        elif isinstance(col.type, _sa.Enum):
            choices = [(e, e) for e in col.type.enums]
            attrs[col_name] = SelectField(lbl, choices=choices, validators=v)
        else:
            attrs[col_name] = StringField(lbl, validators=v)

    from arasCore.lib.forms import ArasForm
    FormCls = type(f"ModelForm_{model.__tablename__}", (ArasForm,), attrs)
    return FormCls(obj=obj) if obj is not None else FormCls()


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
    # Use form_columns() to get mapper-derived columns with FK metadata intact
    fc_map = {cname: col for _, cname, col in model.form_columns()} if hasattr(model, "form_columns") else {}
    rel_maps = {}
    for _, fname in cols:
        col_c = fc_map.get(fname)
        if col_c is None or not col_c.foreign_keys:
            continue
        try:
            fk = list(col_c.foreign_keys)[0]
            ref_tname = fk.column.table.name
            ref_model = _find_ref_model(ref_tname)
            if ref_model:
                rows = ref_model.query.all()
                rel_maps[fname] = {row.id: row_display(row) for row in rows}
        except Exception as _e:
            logger.warning(f"[admin_mount] _build_fk_maps failed for {fname}: {_e}")
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

            cols = res.list_columns or [(lbl, cname) for lbl, cname, _ in model.form_columns()][:6]

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

            # Load per-user saved columns
            saved_columns = None
            try:
                from flask_login import current_user as _cu
                from arasCore.arasAdmin.models import ListViewSetting
                _doctype_key = f"{helper.name}/{res.name}"
                s = ListViewSetting.query.filter_by(
                    user_id=_cu.id, doctype=_doctype_key
                ).first()
                if s:
                    saved_columns = s.columns_json
            except Exception:
                pass

            return render_template(
                "admin/views/adm_list.html",
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
                extra_buttons=res.extra_buttons or [],
                saved_columns=saved_columns,
                doctype_key=f"{helper.name}/{res.name}",
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
            form = _build_model_form(model)
            from arasCore.arasAdmin.services import _invoke_hooks
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
            extra_ctx = {}
            try:
                handler = getattr(self.res, "handler", None)
                if handler and hasattr(handler, "detail_context"):
                    extra_ctx = handler.detail_context(obj) or {}
            except Exception:
                pass

            _app_id, _table_id = self._resolve_app_table_ids()
            
            # Resolve custom layout
            from arasCore.arasAdmin.crud_factory import _parse_layout_tabs
            layout_tabs = _parse_layout_tabs(res_title, None, form, table_id=_table_id)

            return render_template(
                "admin/views/adm_form.html",
                title=f"Add {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/add/",
                list_url=f"{base_url}/",
                show_save_btn=show_save_btn,
                app_id=_app_id,
                table_id=_table_id,
                layout_tabs=layout_tabs,
            )
        return view

    def make_edit(self):
        from arasCore.lib.extensions import db
        model         = self.model
        base_url      = self.base_url
        app_title     = self.app_title
        res_title     = self.res_title
        show_save_btn = getattr(self.res, "show_save_btn", True)
        _helper       = self.helper
        _adm_prefix   = base_url.rsplit("/", 1)[0]  # strip resource segment → adm_prefix

        @login_required
        def view(item_id):
            if not self._rbac("edit"):
                abort(403)
            obj  = model.query.get_or_404(item_id)
            form = _build_model_form(model, obj=obj)
            from arasCore.arasAdmin.services import _invoke_hooks, _get_child_tables_for_model
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
                    # Resolve adm_url from helper resources if not set
                    adm_url = cd.get("adm_url")
                    if not adm_url and _helper:
                        all_res = []
                        for g in (getattr(_helper, "menu_groups", None) or []):
                            all_res.extend(getattr(g, "resources", []))
                        all_res.extend(getattr(_helper, "resources", []) or [])
                        for r in all_res:
                            if getattr(r, "model", None) is cd["model"]:
                                adm_url = f"{_adm_prefix}/{r.name}"
                                break

                    rows = cd["model"].query.filter(
                        getattr(cd["model"], cd["fk_col"]) == item_id
                    ).all()
                    from arasCore.arasAdmin.crud_factory import _build_fk_maps
                    from arasCore.lib.api_handler import get_api_url_for_model
                    from arasCore.arasAdmin.services import _get_inline_columns
                    footer_totals = list(getattr(cd["model"], "__footer_totals__", None) or [])
                    view_in_tab   = bool(getattr(cd["model"], "__view_in_tab__", False))
                    child_tables.append({
                        "title":          cd["title"],
                        "vcols":          cd["vcols"],
                        "adm_url":        adm_url,
                        "fk_col":         cd["fk_col"],
                        "rows":           rows,
                        "parent_id":      item_id,
                        "rel_maps":       _build_fk_maps(cd["vcols"], cd["model"]),
                        "api_url":        get_api_url_for_model(cd["model"]),
                        "inline_columns": _get_inline_columns(cd["model"], cd["fk_col"]),
                        "footer_totals":  footer_totals,
                        "view_in_tab":    view_in_tab,
                    })
                except Exception:
                    pass

            from arasCore.arasAdmin.services import _load_activity_log
            activity_log = _load_activity_log(model.__tablename__, item_id)
            extra_ctx = {}
            try:
                handler = getattr(self.res, "handler", None)
                if handler and hasattr(handler, "detail_context"):
                    extra_ctx = handler.detail_context(obj) or {}
            except Exception:
                pass

            _app_id, _table_id = self._resolve_app_table_ids()
            
            # Resolve custom layout
            from arasCore.arasAdmin.crud_factory import _parse_layout_tabs
            layout_tabs = _parse_layout_tabs(res_title, None, form, table_id=_table_id)

            return render_template(
                "admin/views/adm_form.html",
                title=f"Edit {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/{item_id}/",
                list_url=f"{base_url}/",
                child_tables=child_tables,
                show_save_btn=show_save_btn,
                activity_log=activity_log,
                app_id=_app_id,
                table_id=_table_id,
                layout_tabs=layout_tabs,
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
