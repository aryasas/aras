# -*- coding: utf-8 -*-
"""CRUD view factories, relation helpers, activity log loader."""
import logging

from arasCore.lib.core.extensions import db
from arasCore.lib.ui.label_utils import row_display, find_ref_model as _find_ref_model, humanize as _humanize_label

logger = logging.getLogger(__name__)

_SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at",
                "created_by", "updated_by", "created_by_id", "updated_by_id"}

# ── Hooks & audit ─────────────────────────────────────────────────────────────

def _invoke_hooks(obj, is_new: bool):
    from arasCore.lib.services.audit import maybe_log, _snapshot
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


def _load_activity_log(model_name: str, record_id: int) -> list:
    try:
        from arasCore.admin.models import ArasCoreAuditLog
        from arasCore.auth import User
        entries = (ArasCoreAuditLog.query
                   .filter_by(model_name=model_name, record_id=record_id)
                   .order_by(ArasCoreAuditLog.ts.desc()).limit(50).all())
        user_cache = {}
        result = []
        for e in entries:
            if e.user_id not in user_cache:
                try:
                    u = User.query.get(e.user_id)
                    user_cache[e.user_id] = (
                        getattr(u, "full_name", None) or getattr(u, "username", None) or "Unknown"
                    ) if u else "Unknown"
                except Exception:
                    user_cache[e.user_id] = "Unknown"
            result.append({"ts": e.ts, "user": user_cache[e.user_id], # Original code had e.id which is wrong, changed to e.user_id.
                           "action": e.action, "before": e.before_json, "after": e.after_json})
        return result
    except Exception:
        return []


# ── FK helpers ────────────────────────────────────────────────────────────────

def _build_fk_maps(vcols, model):
    """Build {field_name: {id: label}} maps for FK columns in a vcols list."""
    from sqlalchemy import inspect as sa_inspect
    # Build col→table map from relationships (handles cases where __table__.c FK is empty)
    rel_fk_map: dict[str, str] = {}
    try:
        for rel in sa_inspect(model).relationships:
            if not rel.uselist:
                for _, local_col in rel.synchronize_pairs:
                    rel_fk_map[local_col.name] = rel.mapper.class_.__tablename__
    except Exception:
        pass

    rel_maps = {}
    for _, fname in vcols:
        if fname not in model.__table__.c:
            continue
        col_c = model.__table__.c[fname]
        ref_table_name = None
        if col_c.foreign_keys:
            ref_table_name = list(col_c.foreign_keys)[0].column.table.name
        elif fname in rel_fk_map:
            ref_table_name = rel_fk_map[fname]
        if not ref_table_name:
            continue
        try:
            ref_model = _find_ref_model(ref_table_name)
            if ref_model:
                rel_maps[fname] = {str(r.id): row_display(r) for r in ref_model.query.all()}
        except Exception:
            pass
    return rel_maps


def _get_fk_display_col(model_tablename: str, field_name: str) -> str | None:
    """Return relation_display_col from AppManagerColumn for a FK field, if configured."""
    try:
        from arasCore.admin.models import AppManagerTable
        tbl = AppManagerTable.query.filter_by(db_table_name=model_tablename).first()
        if tbl:
            col = tbl.columns.filter_by(name=field_name).first()
            if col and col.relation_display_col:
                return col.relation_display_col
    except Exception:
        pass
    return None


def _populate_relation_choices(form, model):
    # __fk_choices__: {field_name: callable(query) -> query} on model for per-field filtering
    fk_choices_map = getattr(model, "__fk_choices__", {}) or {}
    for field in form:
        if hasattr(field, "coerce") and field.name.endswith("_id"):
            try:
                fk = list(model.__table__.c[field.name].foreign_keys)[0]
                ref_model = _find_ref_model(fk.column.table.name)
                if ref_model:
                    display_col = _get_fk_display_col(model.__tablename__, field.name)
                    q = ref_model.query
                    if field.name in fk_choices_map:
                        q = fk_choices_map[field.name](q)
                    else:
                        fk_filter = getattr(ref_model, "__fk_filter__", None)
                        if callable(fk_filter):
                            q = fk_filter(q)
                    rows = q.all()
                    if display_col:
                        choices = [(r.id, str(getattr(r, display_col, None) or r.id)) for r in rows]
                    else:
                        choices = [(r.id, row_display(r)) for r in rows]
                    field.choices = [(0, "— Select —")] + choices
                else:
                    field.choices = [(0, "— Select —")]
            except Exception:
                field.choices = [(0, "— Select —")]


# ── Parent/child FK introspection ─────────────────────────────────────────────

def _detect_parent_fk(child_model, parent_model):
    parent_table = parent_model.__tablename__
    try:
        for col in child_model.__table__.columns:
            for fk in col.foreign_keys:
                if fk.column.table.name == parent_table:
                    return col.name
    except Exception:
        pass
    try:
        from sqlalchemy import inspect as sa_inspect
        for rel in sa_inspect(parent_model).relationships:
            if rel.uselist and rel.mapper.class_.__tablename__ == child_model.__tablename__:
                for _, child_col in rel.synchronize_pairs:
                    return child_col.name
    except Exception:
        pass
    return None


def _all_model_columns(model) -> list:
    """Return [(label, field_name)] for ALL non-system, non-PK columns of a model."""
    result = []
    for c in model.__table__.columns:
        if c.name in _SYSTEM_COLS or c.primary_key:
            continue
        result.append((_humanize_label(c.name), c.name))
    return result

def _merge_vcols_into_all_cols(all_cols: list, vcols: list) -> list:
    """Ensure all explicitly requested vcols appear in all_cols for togglers."""
    _all_dict = {fn: lbl for lbl, fn in all_cols}
    for lbl, fn in vcols:
        _all_dict[fn] = lbl

    _merged_all_cols = []
    for _, fn in all_cols:
        _merged_all_cols.append((_all_dict[fn], fn))

    _existing_fns = {fn for _, fn in all_cols}
    for lbl, fn in vcols:
        if fn not in _existing_fns:
            _merged_all_cols.append((lbl, fn))

    return _merged_all_cols


def _smart_vcols(child_cls, fk_col: str, limit: int = 8) -> list:
    """Build vcols prioritising non-FK readable columns; FK _id cols come last."""
    exclude = set(getattr(child_cls, "__vcols_exclude__", None) or set())
    non_fk, fk_cols = [], []
    for c in child_cls.__table__.columns:
        if c.name in _SYSTEM_COLS or c.primary_key or c.name == fk_col or c.name in exclude:
            continue
        entry = (_humanize_label(c.name), c.name)
        if c.foreign_keys:
            fk_cols.append(entry)
        else:
            non_fk.append(entry)
    return (non_fk + fk_cols)[:limit]

def _get_local_child_rows(li_name):
    """Parse ct_local_LI JSON from request.form and return as a list of dicts."""
    from flask import request
    import json
    # Try exact match, then normalized matches
    keys_to_try = [
        f"ct_local_{li_name}",
        f"ct_local_{li_name.lower()}",
        f"ct_local_{li_name.replace('_', '-')}",
        f"ct_local_{li_name.replace('_', '-').lower()}"
    ]
    raw = None
    for k in keys_to_try:
        raw = request.form.get(k)
        if raw:
            break

    if not raw:
        # Last resort: partial match
        for k in request.form.keys():
            if k.startswith("ct_local_") and li_name.lower() in k.lower():
                raw = request.form.get(k)
                break

    if not raw:
        return []
    try:
        data = json.loads(raw)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_local_child_data(obj, model):
    """Process and save ct_local_LI data from request.form for all child tables."""
    from flask import request
    import json
    for cd in _get_child_tables_for_model(model):
        _li = cd["model"].__tablename__
        local_data_str = request.form.get(f"ct_local_{_li}")
        if local_data_str:
            try:
                local_rows = json.loads(local_data_str)
                for row_data in local_rows:
                    child_obj = cd["model"]()
                    setattr(child_obj, cd["fk_col"], obj.id)
                    for k, v in row_data.items():
                        if hasattr(child_obj, k) and k not in ("id", cd["fk_col"]):
                            # Coerce empty values for FKs and numbers
                            if v == "" or v == "0" or v == 0:
                                if k.endswith("_id"):
                                    v = None
                            setattr(child_obj, k, v)
                    db.session.add(child_obj)
            except Exception as parse_ex:
                logger.warning(f"Failed to parse local child data for {_li}: {parse_ex}")


def _get_child_tables_for_model(model):
    from sqlalchemy import inspect as sa_inspect
    from arasCore.lib.services.api_handler import get_api_url_for_model
    from arasCore.admin.models import AppManagerTable
    result = []
    try:
        for rel in sa_inspect(model).relationships:
            if not rel.uselist:
                continue
            child_cls = rel.mapper.class_
            fk_col = _detect_parent_fk(child_cls, model)
            if not fk_col:
                continue
            vcols = _smart_vcols(child_cls, fk_col)
            all_child_cols = _all_model_columns(child_cls)
            all_child_cols = _merge_vcols_into_all_cols(all_child_cols, vcols)
            footer_totals  = list(getattr(child_cls, "__footer_totals__", None) or [])
            view_in_tab    = bool(getattr(child_cls, "__view_in_tab__", False))
            price_api_path = getattr(child_cls, "__price_api_path__", None)
            price_type     = getattr(child_cls, "__price_type__", "sales")
            rel_maps       = _build_fk_maps(vcols, child_cls)

            # ── Find app_id and table_id for the child model ──
            app_id = None
            table_id = None
            tname = child_cls.__tablename__
            mgr_tbl = AppManagerTable.query.filter((AppManagerTable.name == tname) | (AppManagerTable.db_table_name == tname)).first()
            if mgr_tbl:
                app_id = mgr_tbl.app_id
                table_id = mgr_tbl.id

            result.append({
                "title":          child_cls.__tablename__.replace("_", " ").title(),
                "model":          child_cls,
                "vcols":          vcols,
                "all_columns":    all_child_cols,
                "adm_url":        None,
                "fk_col":         fk_col,
                "api_url":        get_api_url_for_model(child_cls),
                "inline_columns": _get_inline_columns(child_cls, fk_col),
                "footer_totals":  footer_totals,
                "view_in_tab":    view_in_tab,
                "price_api_url":  price_api_path,
                "price_type":     price_type,
                "model_name":     child_cls.__tablename__,
                "rel_maps":       rel_maps,
                "app_id":         app_id,
                "table_id":       table_id,
            })
    except Exception:
        pass
    return result


def _get_inline_columns(child_model, fk_col: str) -> list:
    from sqlalchemy import inspect as sa_inspect
    from arasCore.lib.services.api_handler import get_api_url_for_model

    rel_fk_map: dict[str, str] = {}
    try:
        for rel in sa_inspect(child_model).relationships:
            if not rel.uselist:
                for _, local_col in rel.synchronize_pairs:
                    rel_fk_map[local_col.name] = rel.mapper.class_.__tablename__
    except Exception:
        pass

    _type_map = {
        "integer": "number", "float": "number", "numeric": "number",
        "boolean": "checkbox", "text": "textarea", "date": "date",
        "datetime": "datetime-local",
    }
    # Columns that are auto-filled server-side — skip from inline input
    _auto_fill_cols = set()
    _col_names = {c.name for c in child_model.__table__.columns}
    if "invoice_type" in _col_names and "invoice_id" in _col_names:
        _auto_fill_cols.add("invoice_type")

    cols = []
    for col in child_model.__table__.columns:
        if col.primary_key or col.name in _SYSTEM_COLS or col.name == fk_col:
            continue
        if col.name in _auto_fill_cols:
            continue
        input_type = _type_map.get(str(col.type.__class__.__name__).lower(), "text")
        fk_table = fk_api_url = None
        fk_options = []

        raw_fk = (list(col.foreign_keys)[0].column.table.name if col.foreign_keys
                  else rel_fk_map.get(col.name))
        rel_add_url = None
        if raw_fk and raw_fk != "auth_users":
            fk_table = raw_fk
            try:
                ref = _find_ref_model(fk_table)
                if ref:
                    fk_api_url = get_api_url_for_model(ref)
                    fk_options = [
                        {"id": r.id, "label": row_display(r),
                         **({"price_type": r.price_type} if hasattr(r, "price_type") else {})}
                        for r in ref.query.all()
                    ]
                    # Build admin add URL for the referenced table
                    from arasCore.admin.models import AppManagerTable as _AMT, AppManagerApp as _AMA
                    _ref_tbl = _AMT.query.filter(
                        (_AMT.name == raw_fk) | (_AMT.db_table_name == raw_fk)
                    ).first()
                    if _ref_tbl:
                        _ref_app = _AMA.query.get(_ref_tbl.app_id)
                        if _ref_app:
                            rel_add_url = f"/admin{_ref_app.url_prefix}{_ref_tbl.get_full_url(_ref_app.url_prefix)}/add/"
            except Exception:
                pass
            input_type = "select"

        cols.append({
            "name": col.name, "label": _humanize_label(col.name),
            "type": input_type, "required": not col.nullable and col.default is None,
            "fk_table": fk_table, "fk_api_url": fk_api_url, "fk_options": fk_options,
            "rel_add_url": rel_add_url,
        })
    return cols


# ── Layout helper ─────────────────────────────────────────────────────────────

def _parse_layout_tabs(tname, layout_json, form, table_id=None, child_tables=None):
    try:
        from arasCore.lib.ui.layout import _parse_layout_tabs as _do_parse
        return _do_parse(tname, layout_json, form, table_id=table_id, child_tables=child_tables)
    except Exception as e:
        logger.error(f"[crud_factory] Layout parsing failed for {tname}: {e}", exc_info=True)
        return None


# ── Generic CRUD factory ──────────────────────────────────────────────────────

_ACTION_PERM = {"list": "view", "add": "create", "edit": "edit",
                "delete": "delete", "bulk_delete": "delete"}
_ACTION_EVENT = {"add": "created", "edit": "updated", "delete": "deleted"}


def _make_crud_view(action, *, model, form_cls=None, title=None, main_t=None,
                    burl, app_title=None, app_id=None, table_id=None,
                    sibling_tabs=(), app_slug="", req_role=None,
                    tname="", layout_json=None, child_defs=None):
    """
    Generic factory for add / edit / delete / bulk_delete views.
    action: "add" | "edit" | "delete" | "bulk_delete"
    """
    from flask import render_template, redirect, flash, abort, request as _req
    from flask_login import login_required, current_user
    from arasCore.rbac import check_permission

    adm_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]
    perm = _ACTION_PERM.get(action, "view")

    def _check_access():
        if req_role and not current_user.has_role(req_role):
            abort(403)
        if not check_permission(current_user, app_slug, tname, perm):
            abort(403)

    def _emit(event_action, obj):
        try:
            from arasCore.lib.core.events import emit_crud
            emit_crud(app_slug, tname, _ACTION_EVENT[event_action], obj=obj)
        except Exception:
            pass

    # ── add ───────────────────────────────────────────────────────────────────
    if action == "add":
        @login_required
        def view():
            _check_access()
            form = form_cls()
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                obj = model()
                bh, ah = _invoke_hooks(obj, is_new=True)
                bh(); form.populate_obj(obj); db.session.add(obj); db.session.flush()
                _save_local_child_data(obj, model)
                db.session.commit(); ah()
                _emit("add", obj)
                flash("Record added.", "success")
                return redirect(f"{burl}/")
            elif _req.method == "POST":
                for field_name, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {getattr(form, field_name).label.text}: {error}", "danger")

            # Populate rows from ct_local for re-render or GET if needed
            if child_defs:
                for cd in child_defs:
                    cd["rows"] = _get_local_child_rows(cd["model_name"])

            return render_template(
                "admin/gen/gen_view_form.html",
                title=f"Add — {title}", main_title=main_t,
                form=form, action=f"{burl}/add/", list_url=f"{burl}/",
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_tabs, current_tab_url=burl,
                layout_tabs=_parse_layout_tabs(tname, layout_json, form, table_id=table_id, child_tables=child_defs),
                child_tables=child_defs, res_name=tname,
            )
        return view

    # ── edit ──────────────────────────────────────────────────────────────────
    if action == "edit":
        @login_required
        def view(item_id):
            _check_access()
            obj  = model.query.get_or_404(item_id)
            form = form_cls(obj=obj)
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                bh, ah = _invoke_hooks(obj, is_new=False)
                bh(); form.populate_obj(obj);
                _save_local_child_data(obj, model)
                db.session.commit(); ah()
                _emit("edit", obj)
                flash("Record updated.", "success")
                return redirect(f"{burl}/")
            elif _req.method == "POST":
                for field_name, errors in form.errors.items():
                    for error in errors:
                        flash(f"Error in {getattr(form, field_name).label.text}: {error}", "danger")

            # Merge DB rows and local rows for re-render
            if child_defs:
                for cd in child_defs:
                    cd["parent_id"] = item_id
                    db_rows = cd["model"].query.filter(getattr(cd["model"], cd["fk_col"]) == item_id).all()
                    local_rows = _get_local_child_rows(cd["model_name"])
                    cd["rows"] = db_rows + local_rows

            from arasCore.lib.services.api_handler import get_api_url_for_model
            _api_url = get_api_url_for_model(model)
            return render_template(
                "admin/gen/gen_view_form.html",
                title=f"Edit — {title}", main_title=main_t,
                form=form, action=f"{burl}/{item_id}/", list_url=f"{burl}/",
                delete_url=f"{burl}/{item_id}/delete/",
                linked_docs_url=f"{_api_url}{item_id}/linked-docs/" if _api_url else None,
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_tabs, current_tab_url=burl,
                layout_tabs=_parse_layout_tabs(tname, layout_json, form, table_id=table_id, child_tables=child_defs),
                activity_log=_load_activity_log(model.__tablename__, item_id),
                child_tables=child_defs, res_name=tname,
            )
        return view

    # ── delete ────────────────────────────────────────────────────────────────
    if action == "delete":
        @login_required
        def view(item_id):
            _check_access()
            from flask import request as _req, jsonify
            obj = model.query.get_or_404(item_id)
            from arasCore.lib.services.audit import maybe_log, _snapshot
            maybe_log(obj, action="delete", before=_snapshot(obj))
            from arasCore.lib.services.deletion_service import execute_deletion
            from flask_login import current_user as _cu
            try:
                execute_deletion(obj, user_id=getattr(_cu, "id", None))
                _emit("delete", obj)
            except Exception as e:
                db.session.rollback()
                if _req.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return jsonify({"success": False, "message": str(e)}), 400
                flash(str(e), "danger")
                return redirect(f"{burl}/{item_id}/")
            if _req.headers.get("X-Requested-With") == "XMLHttpRequest":
                return jsonify({"success": True, "redirect": f"{burl}/"})
            flash("Record deleted.", "warning")
            return redirect(f"{burl}/")
        return view

    # ── bulk_delete ───────────────────────────────────────────────────────────
    if action == "bulk_delete":
        @login_required
        def view():
            _check_access()
            from flask import request as _req # This was `request` originally, changed to `_req`
            ids = [i.strip() for i in _req.form.get("ids", "").split(",") if i.strip().isdigit()]
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
                        from arasCore.lib.core.extensions import db
                        db.session.rollback()
                        errors.append(str(ex))
            if deleted:
                flash(f"{deleted} record(s) deleted.", "warning")
            for err in errors:
                flash(f"Delete failed: {err}", "danger")
            return redirect(f"{burl}/")
        return view

    raise ValueError(f"Unknown action: {action!r}")


# ── Public shims (called from services._register_table_routes) ────────────────

def make_gen_view_list(model, title, main_t, vcols, adm_burl, app_title, app_id, table_id,
                  sibling_tabs, cur_burl, app_slug, req_role, tname,
                  apply_search_and_filters_fn, layout_json=None, per_page=20):
    return _make_gen_view_list_direct(model, title, main_t, vcols, adm_burl, app_title, app_id,
                                 table_id, sibling_tabs, app_slug, req_role, tname,
                                 apply_search_and_filters_fn, per_page)


def _make_gen_view_list_direct(model, title, main_t, vcols, adm_burl, app_title, app_id,
                           table_id, sibling_tabs, app_slug, req_role, tname,
                           apply_search_fn, per_page):
    from flask import render_template, abort, request as _req
    from flask_login import login_required, current_user
    from arasCore.rbac import check_permission
    adm_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]
    _doctype_key = getattr(model, "__tablename__", tname)

    @login_required
    def view():
        if req_role and not current_user.has_role(req_role):
            abort(403)
        if not check_permission(current_user, app_slug, tname, "view"):
            abort(403)
        eff_pp = per_page
        view_mode = "list"
        show_totals = False
        saved_columns = None
        user_setting = None
        try:
            from arasCore.admin.models import ListViewSetting
            user_setting = ListViewSetting.query.filter_by(
                user_id=current_user.id, doctype=_doctype_key).first()
            if user_setting:
                if user_setting.page_size and user_setting.page_size > 0:
                    eff_pp = user_setting.page_size
                view_mode     = user_setting.view_mode or "list"
                show_totals   = bool(user_setting.show_totals)
                saved_columns = user_setting.columns_json
        except Exception:
            pass
        req_pp = _req.args.get("per_page", type=int)
        if req_pp and req_pp > 0:
            eff_pp = req_pp
            try:
                from arasCore.admin.models import ListViewSetting
                if user_setting is None:
                    user_setting = ListViewSetting(user_id=current_user.id,
                                                   doctype=_doctype_key, page_size=req_pp)
                    db.session.add(user_setting)
                else:
                    user_setting.page_size = req_pp
                db.session.commit()
            except Exception:
                pass
        search_cols = []
        try:
            from arasCore.admin.models import AppManagerColumn
            search_cols = [c.name for c in AppManagerColumn.query.filter_by(
                table_id=table_id, searchable=True).all()]
        except Exception:
            pass
        if not search_cols:
            search_cols = [
                fname for _, fname in vcols
                if fname in model.__table__.c
                and hasattr(model.__table__.c[fname].type, "length")
            ][:5]

        # Fetch saved views for this table
        saved_views = []
        applied_view = None
        try:
            from arasCore.admin.models import AppManagerPageView
            from sqlalchemy import or_
            saved_views = AppManagerPageView.query.filter_by(table_id=table_id).filter(
                or_(AppManagerPageView.owner_id == current_user.id, AppManagerPageView.is_shared == True)
            ).order_by(AppManagerPageView.label).all()

            view_id = _req.args.get("view_id", type=int)
            if view_id:
                applied_view = AppManagerPageView.query.get(view_id)
        except Exception:
            pass

        # ── Sorting logic ──
        sort_col = _req.args.get("sort")
        sort_dir = _req.args.get("dir", "asc")

        if applied_view and not sort_col:
            import json
            try:
                s_json = json.loads(applied_view.sort_json or "{}")
                sort_col = s_json.get("col")
                sort_dir = s_json.get("dir", "asc")
            except Exception: pass

        base_q = model.query
        if sort_col and hasattr(model, sort_col):
            from sqlalchemy import asc, desc
            col_attr = getattr(model, sort_col)
            base_q = base_q.order_by(desc(col_attr) if sort_dir == "desc" else asc(col_attr))
        else:
            if hasattr(model, "id"):
                base_q = base_q.order_by(model.id.desc())

        q_obj, active_filters, search_q = apply_search_fn(base_q, model, search_cols, _req)

        # Apply filters from view if not already filtered by user
        if applied_view and not active_filters and not search_q:
            # TODO: Future enhancement — apply complex filters from applied_view.filter_json
            pass

        current_view = _req.args.get('view', 'list')
        if current_view == 'tree':
            # Force sort by code or id to keep tree consistent
            if hasattr(model, 'code'):
                items = q_obj.order_by(model.code).all()
            else:
                items = q_obj.order_by(model.id).all()
            pagination = None
        else:
            page = _req.args.get("page", 1, type=int)
            pagination = q_obj.paginate(page=page, per_page=eff_pp, error_out=False)
            items = pagination.items

        linked_report_url = None
        try:
            from aras.erp.erp_core.models.report import ErpReport
            _nm = {"acc_sales_invoice": "sales_summary", "acc_purchase_invoice": "purchase_summary",
                   "pos_order": "pot_sales_report", "pos_session": "pos_shift_report"}
            rpt = ErpReport.query.filter_by(name=_doctype_key, is_active=True).first()
            if rpt is None:
                mapped = _nm.get(_doctype_key)
                if mapped:
                    rpt = ErpReport.query.filter_by(name=mapped, is_active=True).first()
            if rpt:
                linked_report_url = f"/admin/erp/reports/{rpt.id}/"
        except Exception:
            pass
        all_cols = _all_model_columns(model)

        # Apply saved column selection if user has a preference or applied view
        if applied_view and applied_view.columns_csv:
            saved_set = set(applied_view.columns_csv.split(","))
            eff_vcols = [(lbl, fn) for lbl, fn in all_cols if fn in saved_set]
            if not eff_vcols:
                eff_vcols = vcols
        elif saved_columns:
            saved_set = set(saved_columns)
            eff_vcols = [(lbl, fn) for lbl, fn in all_cols if fn in saved_set]
            if not eff_vcols:
                eff_vcols = vcols
        else:
            eff_vcols = vcols

        from arasCore.lib.services.api_handler import get_api_url_for_model
        _api_url = get_api_url_for_model(model)

        # Check for workflow
        from arasCore.lib.services.workflow import get_workflow
        _res_key = adm_burl.replace("/admin/", "").strip("/")
        _has_workflow = get_workflow(_res_key) is not None

        return render_template(
            "admin/gen/gen_view_list.html",
            title=title, main_title=main_t,
            items=items, view_columns=eff_vcols,
            pagination=pagination, per_page=eff_pp,
            rel_maps=_build_fk_maps(eff_vcols, model),
            add_url=f"{adm_burl}/add/", edit_url_base=adm_burl, delete_url_base=adm_burl,
            linked_docs_url_base=_api_url,
            workflow_url=f"{adm_burl}/workflow/" if _has_workflow else None,
            app_title=app_title, app_id=app_id, table_id=table_id,
            sibling_tabs=adm_tabs, current_tab_url=adm_burl,
            search_enabled=True, search_q=search_q,
            filter_cols=all_cols, active_filters=active_filters,
            view_mode=view_mode, show_totals=show_totals,
            linked_report_url=linked_report_url,
            doctype_key=_doctype_key, saved_columns=saved_columns,
            all_columns=all_cols,
            saved_views=saved_views,
        )
    return view


def make_adm_add(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id,
                  sibling_tabs, cur_burl, app_slug, req_role, tname, layout_json=None, **kwargs):
    child_defs = kwargs.get("child_defs")
    return _make_crud_view("add", model=model, form_cls=form_cls, title=title, main_t=main_t,
                           burl=adm_burl, app_title=app_title, app_id=app_id, table_id=table_id,
                           sibling_tabs=sibling_tabs, app_slug=app_slug, req_role=req_role,
                           tname=tname, layout_json=layout_json, child_defs=child_defs)


def make_adm_edit(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id,
                  sibling_tabs, cur_burl, app_slug, req_role, tname, layout_json=None, **kwargs):
    child_defs = kwargs.get("child_defs")
    return _make_crud_view("edit", model=model, form_cls=form_cls, title=title, main_t=main_t,
                           burl=adm_burl, app_title=app_title, app_id=app_id, table_id=table_id,
                           sibling_tabs=sibling_tabs, app_slug=app_slug, req_role=req_role,
                           tname=tname, layout_json=layout_json, child_defs=child_defs)

def make_adm_delete(model, adm_burl, app_slug, req_role, tname):
    return _make_crud_view("delete", model=model, burl=adm_burl,
                           app_slug=app_slug, req_role=req_role, tname=tname)


def make_adm_bulk_delete(model, adm_burl, app_slug, req_role, tname):
    return _make_crud_view("bulk_delete", model=model, burl=adm_burl,
                           app_slug=app_slug, req_role=req_role, tname=tname)


def make_adm_workflow(wf, title, app_title, app_id, table_id, sibling_tabs, burl):
    from flask import render_template_string
    from flask_login import login_required
    from arasCore.lib.services.workflow import generate_mermaid

    adm_tabs = [(t, f"/admin{u}") for t, u in sibling_tabs]
    mermaid_code = generate_mermaid(wf)

    @login_required
    def view():
        return render_template_string("""
{% extends 'admin/base_index.html' %}
{% block page_content %}
<div class="aras-studio-theme">
    <div class="container-fluid px-0">
        <div class="aras-header-sticky">
            <div class="aras-header-left">
                <a href="{{ list_url }}" class="aras-back-link"><i class="fa fa-arrow-left"></i></a>
                <h2 class="aras-page-title">Workflow: {{ title }}</h2>
            </div>
            <div class="aras-header-right">
                <a href="{{ list_url }}" class="aras-btn">Back to List</a>
            </div>
        </div>

        <div class="aras-card shadow-sm mt-4">
            <div class="aras-card-header">
                <h3 class="aras-card-title">Visual Workflow Designer</h3>
            </div>
            <div class="aras-card-body text-center py-5">
                <pre class="mermaid" style="background: transparent; border: none;">
{{ mermaid_code }}
                </pre>
            </div>
        </div>

        <div class="aras-card shadow-sm mt-4">
            <div class="aras-card-header">
                <h3 class="aras-card-title">Definition Details</h3>
            </div>
            <div class="aras-card-body">
                <div class="row">
                    <div class="col-md-4">
                        <p><strong>Initial State:</strong> <span class="badge badge-primary">{{ wf.initial }}</span></p>
                        <p><strong>States:</strong> {{ wf.states | join(', ') }}</p>
                    </div>
                    <div class="col-md-8">
                        <h5>Transitions</h5>
                        <table class="table table-sm fs-13">
                            <thead>
                                <tr>
                                    <th>Action</th>
                                    <th>From</th>
                                    <th>To</th>
                                    <th>Roles</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for tr in wf.transitions %}
                                <tr>
                                    <td><code>{{ tr.action }}</code></td>
                                    <td>{{ tr.from_states | join(', ') }}</td>
                                    <td><span class="badge badge-info">{{ tr.to_state }}</span></td>
                                    <td>{{ tr.roles | join(', ') }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block script %}
{{ super() }}
<script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({ startOnLoad: true, theme: 'neutral' });
</script>
{% endblock %}
        """,
        wf=wf, title=title, app_title=app_title, app_id=app_id, table_id=table_id,
        sibling_tabs=adm_tabs, list_url=f"{burl}/", mermaid_code=mermaid_code)

    return view


def make_web_list(model, title, main_t, vcols, burl, app_title, app_id, table_id, sibling_tabs, cur_burl):
    from flask import render_template
    def view():
        return render_template(
            "admin/gen/gen_view_list.html",
            title=title, main_title=main_t,
            items=model.query.all(), view_columns=vcols,
            add_url=f"{burl}/add/", edit_url_base=burl, delete_url_base=burl,
            app_title=app_title, app_id=app_id, table_id=table_id,
            sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
        )
    return view


def make_web_add(model, form_cls, title, main_t, burl, app_title, app_id, table_id, sibling_tabs, cur_burl):
    from flask import render_template, redirect, flash
    from flask_login import login_required

    @login_required
    def view():
        form = form_cls()
        _populate_relation_choices(form, model)
        if form.validate_on_submit():
            obj = model()
            bh, ah = _invoke_hooks(obj, is_new=True)
            bh(); form.populate_obj(obj); db.session.add(obj); db.session.commit(); ah()
            flash("Record added.", "success")
            return redirect(f"{burl}/")
        return render_template(
            "admin/gen/gen_view_form.html",
            title=f"Add — {title}", main_title=f"Add {main_t}",
            form=form, action=f"{burl}/add/", list_url=f"{burl}/",
            app_title=app_title, app_id=app_id, table_id=table_id,
            sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
        )
    return view


def make_web_edit(model, form_cls, title, main_t, burl, app_title, app_id, table_id, sibling_tabs, cur_burl):
    from flask import render_template, redirect, flash
    from flask_login import login_required

    @login_required
    def view(item_id):
        obj  = model.query.get_or_404(item_id)
        form = form_cls(obj=obj)
        _populate_relation_choices(form, model)
        if form.validate_on_submit():
            bh, ah = _invoke_hooks(obj, is_new=False)
            bh(); form.populate_obj(obj); db.session.commit(); ah()
            flash("Record updated.", "success")
            return redirect(f"{burl}/")
        from arasCore.lib.services.api_handler import get_api_url_for_model
        _api_url = get_api_url_for_model(model)
        return render_template(
            "admin/gen/gen_view_form.html",
            title=f"Edit — {title}", main_title=f"Edit {main_t}",
            form=form, action=f"{burl}/{item_id}/", list_url=f"{burl}/",
            delete_url=f"{burl}/{item_id}/delete/",
            linked_docs_url=f"{_api_url}{item_id}/linked-docs/" if _api_url else None,
            app_title=app_title, app_id=app_id, table_id=table_id,
            sibling_tabs=sibling_tabs, current_tab_url=cur_burl,
        )
    return view


def make_web_delete(model, burl):
    from flask import redirect, flash
    from flask_login import login_required

    @login_required
    def view(item_id):
        obj = model.query.get_or_404(item_id)
        from arasCore.lib.services.audit import maybe_log, _snapshot
        maybe_log(obj, action="delete", before=_snapshot(obj))
        db.session.delete(obj); db.session.commit()
        flash("Record deleted.", "warning")
        return redirect(f"{burl}/")
    return view
