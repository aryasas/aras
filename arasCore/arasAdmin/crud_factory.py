# -*- coding: utf-8 -*-
"""CRUD view factories, relation helpers, activity log loader."""
import logging
from arasCore.lib.extensions import db
from arasCore.lib.label_utils import row_display, find_ref_model as _find_ref_model, humanize as _humanize_label

logger = logging.getLogger(__name__)

_SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at",
                "created_by", "updated_by", "created_by_id", "updated_by_id"}

# ── Hooks & audit ─────────────────────────────────────────────────────────────

def _invoke_hooks(obj, is_new: bool):
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


def _load_activity_log(model_name: str, record_id: int) -> list:
    try:
        from arasCore.arasAdmin.models import ArasCoreAuditLog
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
            result.append({"ts": e.ts, "user": user_cache[e.user_id],
                           "action": e.action, "before": e.before_json, "after": e.after_json})
        return result
    except Exception:
        return []


# ── FK helpers ────────────────────────────────────────────────────────────────

def _build_fk_maps(vcols, model):
    """Build {field_name: {id: label}} maps for FK columns in a vcols list."""
    rel_maps = {}
    for _, fname in vcols:
        if fname not in model.__table__.c:
            continue
        col_c = model.__table__.c[fname]
        if not col_c.foreign_keys:
            continue
        try:
            ref_table = list(col_c.foreign_keys)[0].column.table
            ref_model = _find_ref_model(ref_table.name)
            if ref_model:
                rel_maps[fname] = {r.id: row_display(r) for r in ref_model.query.all()}
        except Exception:
            pass
    return rel_maps


def _populate_relation_choices(form, model):
    for field in form:
        if hasattr(field, "coerce") and field.name.endswith("_id"):
            try:
                fk = list(model.__table__.c[field.name].foreign_keys)[0]
                ref_model = _find_ref_model(fk.column.table.name)
                if ref_model:
                    field.choices = [(0, "— Select —")] + [
                        (r.id, row_display(r)) for r in ref_model.query.all()
                    ]
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



def _smart_vcols(child_cls, fk_col: str, limit: int = 5) -> list:
    """Build vcols prioritising non-FK readable columns; FK _id cols come last."""
    non_fk, fk_cols = [], []
    for c in child_cls.__table__.columns:
        if c.name in _SYSTEM_COLS or c.primary_key or c.name == fk_col:
            continue
        entry = (_humanize_label(c.name), c.name)
        if c.foreign_keys:
            fk_cols.append(entry)
        else:
            non_fk.append(entry)
    return (non_fk + fk_cols)[:limit]

def _get_child_tables_for_model(model):
    from sqlalchemy import inspect as sa_inspect
    from arasCore.lib.api_handler import get_api_url_for_model
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
            footer_totals = list(getattr(child_cls, "__footer_totals__", None) or [])
            view_in_tab   = bool(getattr(child_cls, "__view_in_tab__", False))
            result.append({
                "title":          child_cls.__tablename__.replace("_", " ").title(),
                "model":          child_cls,
                "vcols":          vcols,
                "adm_url":        None,
                "fk_col":         fk_col,
                "api_url":        get_api_url_for_model(child_cls),
                "inline_columns": _get_inline_columns(child_cls, fk_col),
                "footer_totals":  footer_totals,
                "view_in_tab":    view_in_tab,
            })
    except Exception:
        pass
    return result


def _get_inline_columns(child_model, fk_col: str) -> list:
    from sqlalchemy import inspect as sa_inspect
    from arasCore.lib.api_handler import get_api_url_for_model

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
    cols = []
    for col in child_model.__table__.columns:
        if col.primary_key or col.name in _SYSTEM_COLS or col.name == fk_col:
            continue
        input_type = _type_map.get(str(col.type.__class__.__name__).lower(), "text")
        fk_table = fk_api_url = None
        fk_options = []

        raw_fk = (list(col.foreign_keys)[0].column.table.name if col.foreign_keys
                  else rel_fk_map.get(col.name))
        if raw_fk and raw_fk != "auth_users":
            fk_table = raw_fk
            try:
                ref = _find_ref_model(fk_table)
                if ref:
                    fk_api_url = get_api_url_for_model(ref)
                    fk_options = [{"id": r.id, "label": row_display(r)} for r in ref.query.all()]
            except Exception:
                pass
            input_type = "select"

        cols.append({
            "name": col.name, "label": _humanize_label(col.name),
            "type": input_type, "required": not col.nullable and col.default is None,
            "fk_table": fk_table, "fk_api_url": fk_api_url, "fk_options": fk_options,
        })
    return cols


# ── Layout helper ─────────────────────────────────────────────────────────────

def _parse_layout_tabs(tname, layout_json, form, table_id=None):
    """
    Resolves the layout structure for the form.
    If table_id is provided, it attempts to fetch the latest layout from DB
    to ensure immediate feedback after saves.
    """
    actual_layout = layout_json
    
    if table_id:
        try:
            from arasCore.arasAdmin.models import AppManagerTable
            # Ensure we are not using a cached version of the object
            tbl = db.session.query(AppManagerTable).filter_by(id=table_id).first()
            if tbl and tbl.layout_json:
                actual_layout = tbl.layout_json
                logger.info(f"[crud_factory] Successfully fetched dynamic layout for {tname} (table_id: {table_id})")
            else:
                logger.debug(f"[crud_factory] No custom layout found in DB for {tname}, using snapshot.")
        except Exception as e:
            logger.warning(f"[crud_factory] Dynamic layout fetch failed for table {table_id}: {e}")

    try:
        from arasCore.lib.layout import _parse_layout_tabs as _do_parse
        result = _do_parse(tname, actual_layout, form)
        if result:
            logger.debug(f"[crud_factory] Parsed {len(result)} tab(s) for {tname}")
        return result
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
            from arasCore.lib.events import emit_crud
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
                bh(); form.populate_obj(obj); db.session.add(obj); db.session.commit(); ah()
                _emit("add", obj)
                flash("Record added.", "success")
                return redirect(f"{burl}/")
            return render_template(
                "admin/views/adm_form.html",
                title=f"Add — {title}", main_title=main_t,
                form=form, action=f"{burl}/add/", list_url=f"{burl}/",
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_tabs, current_tab_url=burl,
                layout_tabs=_parse_layout_tabs(tname, layout_json, form, table_id=table_id),
            )
        return view

    # ── edit ──────────────────────────────────────────────────────────────────
    if action == "edit":
        _child_defs = child_defs or []

        @login_required
        def view(item_id):
            _check_access()
            obj  = model.query.get_or_404(item_id)
            form = form_cls(obj=obj)
            _populate_relation_choices(form, model)
            if form.validate_on_submit():
                bh, ah = _invoke_hooks(obj, is_new=False)
                bh(); form.populate_obj(obj); db.session.commit(); ah()
                _emit("edit", obj)
                flash("Record updated.", "success")
                return redirect(f"{burl}/")

            child_tables = []
            for cd in _child_defs:
                try:
                    rows = cd["model"].query.filter(
                        getattr(cd["model"], cd["fk_col"]) == item_id
                    ).all()
                    child_tables.append({
                        "title":          cd["title"],
                        "vcols":          cd["vcols"],
                        "adm_url":        cd["adm_url"],
                        "fk_col":         cd["fk_col"],
                        "rows":           rows,
                        "parent_id":      item_id,
                        "rel_maps":       _build_fk_maps(cd["vcols"], cd["model"]),
                        "api_url":        cd.get("api_url"),
                        "inline_columns": cd.get("inline_columns", []),
                        "footer_totals":  cd.get("footer_totals", []),
                        "view_in_tab":    cd.get("view_in_tab", False),
                    })
                except Exception:
                    pass

            return render_template(
                "admin/views/adm_form.html",
                title=f"Edit — {title}", main_title=main_t,
                form=form, action=f"{burl}/{item_id}/", list_url=f"{burl}/",
                app_title=app_title, app_id=app_id, table_id=table_id,
                sibling_tabs=adm_tabs, current_tab_url=burl,
                child_tables=child_tables,
                layout_tabs=_parse_layout_tabs(tname, layout_json, form, table_id=table_id),
                activity_log=_load_activity_log(model.__tablename__, item_id),
            )
        return view

    # ── delete ────────────────────────────────────────────────────────────────
    if action == "delete":
        @login_required
        def view(item_id):
            _check_access()
            obj = model.query.get_or_404(item_id)
            from arasCore.lib.audit import maybe_log, _snapshot
            maybe_log(obj, action="delete", before=_snapshot(obj))
            db.session.delete(obj); db.session.commit()
            _emit("delete", obj)
            flash("Record deleted.", "warning")
            return redirect(f"{burl}/")
        return view

    # ── bulk_delete ───────────────────────────────────────────────────────────
    if action == "bulk_delete":
        @login_required
        def view():
            _check_access()
            ids = [i.strip() for i in _req.form.get("ids", "").split(",") if i.strip().isdigit()]
            deleted = 0
            for id_str in ids:
                obj = model.query.get(int(id_str))
                if obj:
                    try:
                        from arasCore.lib.audit import maybe_log, _snapshot
                        maybe_log(obj, action="delete", before=_snapshot(obj))
                        db.session.delete(obj); deleted += 1
                    except Exception:
                        pass
            try:
                db.session.commit()
                flash(f"{deleted} record(s) deleted.", "warning")
            except Exception as ex:
                db.session.rollback()
                flash(str(ex), "danger")
            return redirect(f"{burl}/")
        return view

    raise ValueError(f"Unknown action: {action!r}")


# ── Public shims (called from services._register_table_routes) ────────────────

def make_adm_list(model, title, main_t, vcols, adm_burl, app_title, app_id, table_id,
                  sibling_tabs, cur_burl, app_slug, req_role, tname,
                  apply_search_and_filters_fn, layout_json=None, per_page=20):
    return _make_adm_list_direct(model, title, main_t, vcols, adm_burl, app_title, app_id,
                                 table_id, sibling_tabs, app_slug, req_role, tname,
                                 apply_search_and_filters_fn, per_page)


def _make_adm_list_direct(model, title, main_t, vcols, adm_burl, app_title, app_id,
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
            from arasCore.arasAdmin.models import ListViewSetting
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
                from arasCore.arasAdmin.models import ListViewSetting
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
            from arasCore.arasAdmin.models import AppManagerColumn
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
        q_obj, active_filters, search_q = apply_search_fn(model.query.order_by(model.id.desc()), model, search_cols, _req)
        page = _req.args.get("page", 1, type=int)
        pagination = q_obj.paginate(page=page, per_page=eff_pp, error_out=False)
        linked_report_url = None
        try:
            from aras.app_erp.erp_core.models.report import ErpReport
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
        return render_template(
            "admin/views/adm_list.html",
            title=title, main_title=main_t,
            items=pagination.items, view_columns=vcols,
            pagination=pagination, per_page=eff_pp,
            rel_maps=_build_fk_maps(vcols, model),
            add_url=f"{adm_burl}/add/", edit_url_base=adm_burl, delete_url_base=adm_burl,
            app_title=app_title, app_id=app_id, table_id=table_id,
            sibling_tabs=adm_tabs, current_tab_url=adm_burl,
            search_enabled=True, search_q=search_q,
            filter_cols=list(vcols), active_filters=active_filters,
            view_mode=view_mode, show_totals=show_totals,
            linked_report_url=linked_report_url,
            doctype_key=_doctype_key, saved_columns=saved_columns,
        )
    return view


def make_adm_add(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id,
                 sibling_tabs, cur_burl, app_slug, req_role, tname, layout_json=None):
    return _make_crud_view("add", model=model, form_cls=form_cls, title=title, main_t=main_t,
                           burl=adm_burl, app_title=app_title, app_id=app_id, table_id=table_id,
                           sibling_tabs=sibling_tabs, app_slug=app_slug, req_role=req_role,
                           tname=tname, layout_json=layout_json)


def make_adm_edit(model, form_cls, title, main_t, adm_burl, app_title, app_id, table_id,
                  sibling_tabs, cur_burl, app_slug, req_role, tname, layout_json=None, child_defs=None):
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


def make_web_list(model, title, main_t, vcols, burl, app_title, app_id, table_id, sibling_tabs, cur_burl):
    from flask import render_template
    def view():
        return render_template(
            "admin/views/adm_list.html",
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
            "admin/views/adm_form.html",
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
        return render_template(
            "admin/views/adm_form.html",
            title=f"Edit — {title}", main_title=f"Edit {main_t}",
            form=form, action=f"{burl}/{item_id}/", list_url=f"{burl}/",
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
        from arasCore.lib.audit import maybe_log, _snapshot
        maybe_log(obj, action="delete", before=_snapshot(obj))
        db.session.delete(obj); db.session.commit()
        flash("Record deleted.", "warning")
        return redirect(f"{burl}/")
    return view
