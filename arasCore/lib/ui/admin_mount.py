"""
arasCore/lib/admin_mount.py — AdminResourceMounter

Extracted from blueprints._mount_admin_resource to eliminate nested closures
and make each CRUD action a discrete, testable method.
"""
import logging

from flask import render_template, redirect, flash, abort, request
from flask_login import login_required

logger = logging.getLogger(__name__)


from arasCore.lib.ui.label_utils import humanize, row_display, find_ref_model as _find_ref_model


def _fk_coerce(x):
    try:
        v = int(x)
        return v if v != 0 else None
    except (TypeError, ValueError):
        return None


def _fix_fk_zeros(obj, model):
    """Null any nullable FK column on `obj` whose value is 0 (the SelectField sentinel).

    Runs after form.populate_obj() to defend against any code path that lets the
    0-sentinel reach SQLAlchemy. Non-nullable FK=0 is left as-is so the DB raises
    a clear constraint error instead of silently nulling.
    """
    try:
        for sa_col in model.__table__.columns:
            if not sa_col.foreign_keys or not sa_col.nullable:
                continue
            name = sa_col.key
            if getattr(obj, name, None) == 0:
                setattr(obj, name, None)
    except Exception as _e:
        logger.debug(f"[admin_mount] _fix_fk_zeros failed: {_e}")


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


def _preview_doc_series_name(form, model):
    """Pre-fill the form's name field with the next DocSeries number (no commit).
    Reads main_doc_series row by code=__tablename__, company_id IS NULL.
    Falls back to model.__naming_series__ if no row found.
    """
    try:
        from sqlalchemy import text
        from datetime import date
        from arasCore.lib.core.extensions import db
        name_field = getattr(model, "__name_field__", "name")
        if not isinstance(getattr(form, "data", None), dict):
            return
        if form.data.get(name_field):
            return
        tbl = getattr(model, "__tablename__", "")
        row = db.session.execute(
            text("SELECT format, next_value, last_period, padding, prefix, suffix "
                 "FROM main_doc_series WHERE code=:c AND company_id IS NULL AND is_active=1"),
            {"c": tbl},
        ).first()
        today = date.today()
        year, month, day = today.year, today.month, today.day
        if row:
            fmt = row[0] or model.__naming_series__
            num = row[1] if row[2] == str(year) else 1
            pad = row[3] or 4
            prefix = row[4] or ""
            suffix = row[5] or ""
        else:
            fmt = model.__naming_series__
            num, pad = 1, 4
            prefix = suffix = ""
        import re
        out = (fmt
            .replace("{prefix}", prefix)
            .replace("{suffix}", suffix)
            .replace("{YYYY}", f"{year:04d}")
            .replace("{YY}", f"{year % 100:02d}")
            .replace("{MM}", f"{month:02d}")
            .replace("{DD}", f"{day:02d}")
            .replace("{seq}", f"{num:0{pad}d}"))
        out = re.sub(r"\{(#+)\}", lambda m: f"{num:0{len(m.group(1))}d}", out)
        form.data[name_field] = out.strip("/")
    except Exception:
        pass


def _build_model_form(model, obj=None, *, data=None):
    """Single source of truth: return an ArasForm bound to this model.

    No WTForms anywhere. The form is a dict-driven schema (see ArasForm).
    Templates iterate ``form.fields`` (list of dicts from Col.to_schema()).
    FK choices are resolved per-request and attached to the schema dict.
    """
    if hasattr(model, "form") and callable(getattr(model, "form")):
        form = model.form(data=data, obj=obj)
    else:
        from arasCore.arasgen import ArasForm
        FormCls = ArasForm.from_model(model)
        form = FormCls(data=data, obj=obj)

    # Resolve FK choices once per request and merge into schema dicts so
    # the template renderer can populate <select> options without re-querying.
    try:
        for fname, col in form._aras_fields.items():
            if not col.fk:
                continue
            try:
                ref_tname = col.fk.split(".")[0]
                ref_model = _find_ref_model(ref_tname)
                if ref_model:
                    rows = ref_model.query.order_by(ref_model.id).all()
                    col._fk_choices = [(0, "— Select —")] + [(r.id, row_display(r)) for r in rows]
            except Exception as _e:
                logger.debug(f"[admin_mount] fk choices fail {fname}: {_e}")
    except Exception:
        pass

    return form



def _resolve_search_cols(helper, res, model):
    """Get searchable column names for a resource."""
    search_cols = []
    try:
        from arasCore.admin.models import AppManagerApp, AppManagerTable, AppManagerColumn
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


from arasCore.admin.crud_factory import _get_local_child_rows, _save_local_child_data


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
                rel_maps[fname] = {str(row.id): row_display(row) for row in rows}
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
            from arasCore.admin.models import AppManagerApp, AppManagerTable
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

            from arasCore.admin.services import apply_search_and_filters
            q_obj, active_filters, search_q = apply_search_and_filters(
                model.query.order_by(model.id.desc()), model, search_cols, _req
            )

            current_view = _req.args.get('view', 'list')
            if current_view == 'tree':
                if hasattr(model, 'code'):
                    items = q_obj.order_by(model.code).all()
                else:
                    items = q_obj.order_by(model.id).all()
                pagination = None
            else:
                page = _req.args.get("page", 1, type=int)
                pagination = q_obj.paginate(page=page, per_page=20, error_out=False)
                items = pagination.items

            rel_maps = _build_fk_maps(cols, model)

            # Load per-user saved columns
            saved_columns = None
            try:
                from flask_login import current_user as _cu
                from arasCore.admin.models import ListViewSetting
                _doctype_key = f"{helper.name}/{res.name}"
                s = ListViewSetting.query.filter_by(
                    user_id=_cu.id, doctype=_doctype_key
                ).first()
                if s:
                    import json
                    saved_columns = json.loads(s.columns_json) if s.columns_json else None
            except Exception:
                pass

            from arasCore.admin.crud_factory import _all_model_columns, _merge_vcols_into_all_cols
            all_cols = _all_model_columns(model)
            all_cols = _merge_vcols_into_all_cols(all_cols, cols)

            # Apply saved column preference to view_columns
            if saved_columns:
                saved_set = set(saved_columns)
                eff_cols = [(lbl, fn) for lbl, fn in all_cols if fn in saved_set]
                if eff_cols:
                    cols = eff_cols
                    rel_maps = _build_fk_maps(cols, model)

            from arasCore.lib.services.api_handler import get_api_url_for_model
            _api_url = get_api_url_for_model(model)
            return render_template(
                "admin/gen/gen_view_list.html",
                title=res_title,
                main_title=res_title,
                items=items,
                view_columns=cols,
                all_columns=all_cols,
                pagination=pagination,
                rel_maps=rel_maps,
                add_url=f"{base_url}/add/",
                edit_url_base=base_url,
                delete_url_base=base_url,
                linked_docs_url_base=_api_url,
                app_id=_app_id,
                table_id=_table_id,
                search_enabled=True,
                search_q=search_q,
                filter_cols=all_cols,
                active_filters=active_filters,
                extra_buttons=res.extra_buttons or [],
                saved_columns=saved_columns,
                doctype_key=f"{helper.name}/{res.name}",
            )
        return view

    def make_add(self):
        from arasCore.lib.core.extensions import db
        model         = self.model
        base_url      = self.base_url
        app_title     = self.app_title
        res_title     = self.res_title
        show_save_btn = getattr(self.res, "show_save_btn", True)
        _helper       = self.helper
        _adm_prefix   = base_url.rsplit("/", 1)[0]

        @login_required
        def view():
            if not self._rbac("create"):
                abort(403)
            form = _build_model_form(model)
            from arasCore.admin.services import _invoke_hooks, _get_child_tables_for_model
            # Preview auto-name from DocSeries config (DB-driven, user-customizable)
            if request.method == "GET" and getattr(model, "__naming_series__", None):
                _preview_doc_series_name(form, model)
                logger.warning(f"[autoname-debug] {model.__tablename__}: name={form.data.get('name')!r}")
            if form.validate_on_submit():
                try:
                    obj = model()
                    logger.info(f"[admin_mount] Add {model.__tablename__}: partner_id={form.partner_id.data if hasattr(form, 'partner_id') else 'N/A'}")
                    before_hook, after_hook = _invoke_hooks(obj, is_new=True)
                    before_hook()
                    form.populate_obj(obj)
                    _fix_fk_zeros(obj, model)
                    db.session.add(obj)
                    db.session.flush()

                    _save_local_child_data(obj, model)

                    after_hook()
                    db.session.commit()
                    flash("Record created.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    logger.exception(f"[admin_mount] Save failed for {model.__tablename__}")
                    flash(f"Save failed ({type(ex).__name__}): {ex}", "danger")
            elif request.method == "POST":
                if not form.errors:
                    flash("Save failed: form did not validate (no field errors). Check CSRF token / required fields.", "danger")
                for field_name, errors in form.errors.items():
                    errs = errors if isinstance(errors, (list, tuple)) else [errors]
                    for err in errs:
                        try:
                            label = getattr(form, field_name).label.text
                        except Exception:
                            label = field_name
                        flash(f"{label}: {err}", "danger")

            child_tables = []
            for cd in _get_child_tables_for_model(model):
                try:
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

                    from arasCore.admin.crud_factory import _build_fk_maps, _all_model_columns
                    from arasCore.lib.services.api_handler import get_api_url_for_model
                    from arasCore.admin.services import _get_inline_columns

                    all_child_cols = cd.get("all_columns") or _all_model_columns(cd["model"])
                    vcols = cd["vcols"]

                    _ct_app_id, _ct_table_id = cd.get("app_id"), cd.get("table_id")
                    if not _ct_table_id:
                        try:
                            from arasCore.admin.models import AppManagerApp, AppManagerTable
                            _ct_app_rec = AppManagerApp.query.filter_by(url=getattr(_helper, "admin_slug", getattr(_helper, "name", None))).first() if _helper else None
                            if _ct_app_rec:
                                _ct_tbl_rec = AppManagerTable.query.filter_by(app_id=_ct_app_rec.id, db_table_name=cd["model"].__tablename__).first()
                                _ct_app_id  = _ct_app_rec.id
                                _ct_table_id = _ct_tbl_rec.id if _ct_tbl_rec else None
                        except Exception:
                            pass

                    child_tables.append({
                        "title":                   cd["title"],
                        "vcols":                   vcols,
                        "all_columns":             all_child_cols,
                        "adm_url":                 adm_url,
                        "fk_col":                  cd["fk_col"],
                        "rows":                    _get_local_child_rows(cd["model"].__tablename__),
                        "parent_id":               None,
                        "rel_maps":                _build_fk_maps(vcols, cd["model"]),
                        "api_url":                 get_api_url_for_model(cd["model"]) or (f"/api/{_helper.api_slug}/{cd['model'].__tablename__.replace('_', '-')}/" if _helper else None),
                        "inline_columns":          _get_inline_columns(cd["model"], cd["fk_col"]),
                        "footer_totals":           list(getattr(cd["model"], "__footer_totals__", None) or []),
                        "view_in_tab":             bool(getattr(cd["model"], "__view_in_tab__", False)),
                        "model_name":              cd["model"].__tablename__,
                        "price_api_url":           cd.get("price_api_url"),
                        "price_type":              cd.get("price_type", "sales"),
                        "parent_company_id":       None,
                        "parent_price_list_field": "#price_type_id",
                        "app_id":                  _ct_app_id,
                        "table_id":                _ct_table_id,
                        "parent_model_name":       model.__tablename__,
                    })
                except Exception:
                    pass

            handler   = getattr(self.res, "handler", None)
            extra_ctx = {}
            try:
                if handler and hasattr(handler, "detail_context"):
                    extra_ctx = handler.detail_context(None) or {}
            except Exception:
                pass

            # Inject child_table_actions per child table
            if handler and hasattr(handler, "child_table_actions"):
                for _cd in child_tables:
                    try:
                        _cd["custom_actions"] = handler.child_table_actions(_cd["model_name"], None) or []
                    except Exception:
                        _cd["custom_actions"] = []

            _app_id, _table_id = self._resolve_app_table_ids()

            from arasCore.admin.crud_factory import _parse_layout_tabs
            layout_tabs = _parse_layout_tabs(res_title, None, form, table_id=_table_id, child_tables=child_tables)

            return render_template(
                "admin/gen/gen_view_form.html",
                title=f"Add {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/add/",
                list_url=f"{base_url}/",
                child_tables=child_tables,
                show_save_btn=show_save_btn,
                readonly_fields=set(getattr(model, "__readonly_fields__", None) or []),
                app_id=_app_id,
                table_id=_table_id,
                layout_tabs=layout_tabs,
                **extra_ctx,
            )
        return view

    def make_edit(self):
        from arasCore.lib.core.extensions import db
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
            from arasCore.admin.services import _invoke_hooks, _get_child_tables_for_model
            if form.validate_on_submit():
                try:
                    logger.info(f"[admin_mount] Edit {model.__tablename__} {item_id}: partner_id={form.partner_id.data if hasattr(form, 'partner_id') else 'N/A'}")
                    before_hook, after_hook = _invoke_hooks(obj, is_new=False)
                    before_hook()
                    form.populate_obj(obj)
                    _fix_fk_zeros(obj, model)

                    _save_local_child_data(obj, model)

                    after_hook()
                    db.session.commit()
                    flash("Record updated.", "success")
                    return redirect(f"{base_url}/")
                except Exception as ex:
                    db.session.rollback()
                    logger.exception(f"[admin_mount] Save failed for {model.__tablename__}")
                    flash(f"Save failed ({type(ex).__name__}): {ex}", "danger")
            elif request.method == "POST":
                if not form.errors:
                    flash("Save failed: form did not validate (no field errors). Check CSRF token / required fields.", "danger")
                for field_name, errors in form.errors.items():
                    errs = errors if isinstance(errors, (list, tuple)) else [errors]
                    for err in errs:
                        try:
                            label = getattr(form, field_name).label.text
                        except Exception:
                            label = field_name
                        flash(f"{label}: {err}", "danger")

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

                    db_rows = cd["model"].query.filter(
                        getattr(cd["model"], cd["fk_col"]) == item_id
                    ).all()
                    local_rows = _get_local_child_rows(cd["model"].__tablename__)
                    rows = db_rows + local_rows

                    from arasCore.admin.crud_factory import _build_fk_maps
                    from arasCore.lib.services.api_handler import get_api_url_for_model
                    from arasCore.admin.services import _get_inline_columns
                    footer_totals = list(getattr(cd["model"], "__footer_totals__", None) or [])
                    view_in_tab   = bool(getattr(cd["model"], "__view_in_tab__", False))
                    # Load per-user saved columns for child table
                    ct_saved_columns = None
                    try:
                        from flask_login import current_user as _cu
                        from arasCore.admin.models import ListViewSetting
                        _ct_doctype_key = f"child/{cd['model'].__tablename__}"
                        cts = ListViewSetting.query.filter_by(
                            user_id=_cu.id, doctype=_ct_doctype_key
                        ).first()
                        if cts:
                            import json
                            ct_saved_columns = json.loads(cts.columns_json) if cts.columns_json else None
                    except Exception:
                        pass

                    from arasCore.admin.crud_factory import _all_model_columns
                    all_child_cols = cd.get("all_columns") or _all_model_columns(cd["model"])

                    if ct_saved_columns:
                        saved_set = set(ct_saved_columns)
                        eff_vcols = [(lbl, fn) for lbl, fn in all_child_cols if fn in saved_set]
                        if not eff_vcols:
                            eff_vcols = cd["vcols"]
                    else:
                        eff_vcols = cd["vcols"]

                    _parent_company_id = getattr(obj, "company_id", None)
                    _ct_app_id, _ct_table_id = cd.get("app_id"), cd.get("table_id")
                    if not _ct_table_id:
                        try:
                            from arasCore.admin.models import AppManagerApp, AppManagerTable
                            _ct_app_rec = AppManagerApp.query.filter_by(url=getattr(_helper, "admin_slug", getattr(_helper, "name", None))).first() if _helper else None
                            if _ct_app_rec:
                                _ct_tbl_rec = AppManagerTable.query.filter_by(app_id=_ct_app_rec.id, db_table_name=cd["model"].__tablename__).first()
                                _ct_app_id  = _ct_app_rec.id
                                _ct_table_id = _ct_tbl_rec.id if _ct_tbl_rec else None
                        except Exception:
                            pass

                    child_tables.append({
                        "title":                   cd["title"],
                        "vcols":                   eff_vcols,
                        "all_columns":             all_child_cols,
                        "adm_url":                 adm_url,
                        "fk_col":                  cd["fk_col"],
                        "rows":                    rows,
                        "parent_id":               item_id,
                        "rel_maps":                _build_fk_maps(eff_vcols, cd["model"]),
                        "api_url":                 get_api_url_for_model(cd["model"]) or (f"/api/{_helper.api_slug}/{cd['model'].__tablename__.replace('_', '-')}/" if _helper else None),
                        "inline_columns":          _get_inline_columns(cd["model"], cd["fk_col"]),
                        "footer_totals":           footer_totals,
                        "view_in_tab":             view_in_tab,
                        "model_name":              cd["model"].__tablename__,
                        "saved_columns":           ct_saved_columns,
                        "price_api_url":           cd.get("price_api_url"),
                        "price_type":              cd.get("price_type", "sales"),
                        "parent_company_id":       _parent_company_id,
                        "parent_price_list_field": "#price_type_id",
                        "app_id":                  _ct_app_id,
                        "table_id":                _ct_table_id,
                        "parent_model_name":       model.__tablename__,
                    })
                except Exception:
                    pass

            from arasCore.admin.services import _load_activity_log
            activity_log = _load_activity_log(model.__tablename__, item_id)
            handler   = getattr(self.res, "handler", None)
            extra_ctx = {}
            try:
                if handler and hasattr(handler, "detail_context"):
                    extra_ctx = handler.detail_context(obj) or {}
                # Inject custom_actions list into extra_ctx for generic toolbar rendering
                if "custom_actions" not in extra_ctx:
                    extra_ctx["custom_actions"] = extra_ctx.pop("custom_actions", [])
            except Exception as _e:
                import logging; logging.getLogger(__name__).warning(f"[admin_mount] detail_context error: {_e}")
            # Inject child_table_actions per child table
            if handler and hasattr(handler, "child_table_actions"):
                for _cd in child_tables:
                    try:
                        _cd["custom_actions"] = handler.child_table_actions(_cd["model_name"], obj) or []
                    except Exception:
                        _cd["custom_actions"] = []

            _app_id, _table_id = self._resolve_app_table_ids()

            # Resolve custom layout
            from arasCore.admin.crud_factory import _parse_layout_tabs
            layout_tabs = _parse_layout_tabs(res_title, None, form, table_id=_table_id, child_tables=child_tables)

            _readonly_fields = set(getattr(model, "__readonly_fields__", None) or [])
            # Build linked-docs preview URL for delete dialog
            from arasCore.lib.services.api_handler import get_api_url_for_model
            _api_url = get_api_url_for_model(model)
            _linked_docs_url = f"{_api_url}{item_id}/linked-docs/" if _api_url else None
            return render_template(
                "admin/gen/gen_view_form.html",
                title=f"Edit {res_title}",
                main_title=app_title,
                form=form,
                action=f"{base_url}/{item_id}/",
                delete_url=f"{base_url}/{item_id}/delete/",
                list_url=f"{base_url}/",
                child_tables=child_tables,
                readonly_fields=_readonly_fields,
                show_save_btn=show_save_btn,
                activity_log=activity_log,
                app_id=_app_id,
                table_id=_table_id,
                layout_tabs=layout_tabs,
                linked_docs_url=_linked_docs_url,
                **extra_ctx,
            )
        return view

    def make_delete(self):
        from arasCore.lib.core.extensions import db
        model    = self.model
        base_url = self.base_url

        @login_required
        def view(item_id):
            if not self._rbac("delete"):
                abort(403)
            obj = model.query.get_or_404(item_id)
            try:
                from arasCore.lib.services.audit import maybe_log, _snapshot
                maybe_log(obj, action="delete", before=_snapshot(obj))
                from arasCore.lib.services.deletion_service import execute_deletion
                from flask_login import current_user as _cu
                execute_deletion(obj, user_id=getattr(_cu, "id", None))
                flash("Record deleted.", "warning")
            except Exception as ex:
                db.session.rollback()
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return {"success": False, "message": str(ex)}, 400
                flash(str(ex), "danger")

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {"success": True, "message": "Record deleted."}
            return redirect(f"{base_url}/")
        return view

    def make_bulk_delete(self):
        from arasCore.lib.core.extensions import db
        from flask import request
        model    = self.model
        base_url = self.base_url

        @login_required
        def view():
            if not self._rbac("delete"):
                abort(403)
            raw = request.form.get("ids", "")
            if not raw and request.is_json:
                raw = request.json.get("ids", "")

            ids = [i.strip() for i in raw.split(",") if i.strip().isdigit()]
            deleted = 0
            errors  = []
            for id_str in ids:
                obj = model.query.get(int(id_str))
                if obj:
                    try:
                        from arasCore.lib.services.audit import maybe_log, _snapshot
                        maybe_log(obj, action="delete", before=_snapshot(obj))
                        from arasCore.lib.services.deletion_service import execute_deletion
                        from flask_login import current_user as _cu
                        execute_deletion(obj, user_id=getattr(_cu, "id", None))
                        deleted += 1
                    except Exception as ex:
                        db.session.rollback()
                        errors.append(str(ex))

            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return {
                    "success": len(errors) == 0,
                    "deleted": deleted,
                    "errors": errors,
                    "message": f"{deleted} record(s) deleted."
                }

            if deleted:
                flash(f"{deleted} record(s) deleted.", "warning")
            for err in errors:
                flash(f"Delete failed: {err}", "danger")
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

            from arasCore.lib.services.workflow import get_workflow
            from arasCore.admin.crud_factory import make_adm_workflow
            api_slug = self.helper.api_slug if getattr(self.helper, "api_slug", None) else self.helper.name
            wf = get_workflow(f"{api_slug}/{self.res.name}")
            if wf:
                self.bp.add_url_rule(f"{url}/workflow/", endpoint=f"{ep}_workflow", view_func=make_adm_workflow(wf, self.res.menu_title or self.res.name, self.helper.title, None, None, [], url))

        except Exception as ex:
            logger.error(f"[admin_mount] failed to mount {url}: {ex}")
