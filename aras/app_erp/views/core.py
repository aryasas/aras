import json
import csv
import io
from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from . import app_bp
from arasCore.lib.extensions import db


def _get_company_id():
    from aras.app_erp.erp_core.models.company import CoreCompany
    cid = getattr(current_user, "company_id", None)
    if not cid:
        company = CoreCompany.query.filter_by(is_active=True).order_by(CoreCompany.id).first()
        cid = company.id if company else None
    return cid


# # ── TASK 1: Journal Entry detail ─────────────────────────────────────────────

# @app_bp.route("/acc/entry/<int:item_id>/")
# @login_required
# def journal_entry_detail(item_id):
#     from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
#     entry = AccJournalEntry.query.get_or_404(item_id)
#     lines = (
#         AccJournalLine.query
#         .filter_by(entry_id=item_id)
#         .order_by(AccJournalLine.sequence)
#         .all()
#     )
#     return render_template(
#         "erp/acc/journal_entry_detail.html",
#         entry=entry,
#         lines=lines,
#         main_title="Journal Entry",
#     )


# # ── TASK 2c: List-view setting API ───────────────────────────────────────────

# @app_bp.route("/api/list-view-setting/", methods=["POST"])
# @login_required
# def api_save_list_view_setting():
#     from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
#     data = request.get_json() or {}
#     doctype = data.get("doctype")
#     if not doctype:
#         return jsonify({"ok": False, "error": "doctype required"}), 400

#     setting = ErpListViewSetting.query.filter_by(
#         user_id=current_user.id, doctype=doctype
#     ).first()
#     if not setting:
#         setting = ErpListViewSetting(user_id=current_user.id, doctype=doctype)
#         db.session.add(setting)

#     if "columns" in data:
#         setting.columns_json = json.dumps(data["columns"])
#     if "filters" in data:
#         setting.filters_json = json.dumps(data["filters"])
#     if "page_size" in data:
#         setting.page_size = int(data["page_size"])

#     db.session.commit()
#     return jsonify({"ok": True})


# @app_bp.route("/api/list-view-setting/<doctype>/")
# @login_required
# def api_get_list_view_setting(doctype):
#     from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
#     setting = ErpListViewSetting.query.filter_by(
#         user_id=current_user.id, doctype=doctype
#     ).first()
#     if not setting:
#         return jsonify({"ok": True, "data": None})
#     return jsonify({
#         "ok": True,
#         "data": {
#             "columns":   json.loads(setting.columns_json)  if setting.columns_json  else None,
#             "filters":   json.loads(setting.filters_json)  if setting.filters_json  else None,
#             "page_size": setting.page_size,
#         },
#     })


# ── TASK 2d: Sales Invoice list ───────────────────────────────────────────────

# @app_bp.route("/acc/sales-invoice/")
# @login_required
# def sales_invoice_list():
#     from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice
#     from aras.app_erp.erp_crm.models.customer import CrmCustomer

#     search    = request.args.get("search", "")
#     state     = request.args.get("state", "")
#     date_from = request.args.get("date_from", "")
#     date_to   = request.args.get("date_to", "")
#     page      = int(request.args.get("page", 1))
#     per_page  = int(request.args.get("per_page", 20))

#     q = AccSalesInvoice.query
#     if search:
#         q = q.join(CrmCustomer).filter(
#             db.or_(
#                 AccSalesInvoice.name.ilike(f"%{search}%"),
#                 CrmCustomer.name.ilike(f"%{search}%"),
#             )
#         )
#     if state:
#         q = q.filter(AccSalesInvoice.state == state)
#     if date_from:
#         q = q.filter(AccSalesInvoice.invoice_date >= date_from)
#     if date_to:
#         q = q.filter(AccSalesInvoice.invoice_date <= date_to)

#     q = q.order_by(AccSalesInvoice.invoice_date.desc())
#     pagination = q.paginate(page=page, per_page=per_page, error_out=False)

#     columns = [
#         {"field": "name",     "label": "Invoice No", "visible": True},
#         {"field": "customer", "label": "Customer",   "visible": True},
#         {"field": "date",     "label": "Date",       "visible": True},
#         {"field": "total",    "label": "Total",      "visible": True},
#         {"field": "state",    "label": "State",      "visible": True},
#     ]

#     return render_template(
#         "erp/acc/sales_invoice_list.html",
#         items=pagination.items,
#         pagination=pagination,
#         columns=columns,
#         doctype="acc_sales_invoice",
#         title="Sales Invoices",
#         new_url="/admin/erp/acc/sales-invoice/add/",
#         reports=[],
#         filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
#         main_title="Sales Invoices",
#     )


# # ── TASK 2d: Purchase Invoice list ────────────────────────────────────────────

# @app_bp.route("/acc/purchase-invoice/")
# @login_required
# def purchase_invoice_list():
#     from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice

#     search    = request.args.get("search", "")
#     state     = request.args.get("state", "")
#     date_from = request.args.get("date_from", "")
#     date_to   = request.args.get("date_to", "")
#     page      = int(request.args.get("page", 1))
#     per_page  = int(request.args.get("per_page", 20))

#     q = AccPurchaseInvoice.query
#     if search:
#         q = q.filter(
#             db.or_(
#                 AccPurchaseInvoice.name.ilike(f"%{search}%"),
#                 AccPurchaseInvoice.vendor_name.ilike(f"%{search}%"),
#             )
#         )
#     if state:
#         q = q.filter(AccPurchaseInvoice.state == state)
#     if date_from:
#         q = q.filter(AccPurchaseInvoice.invoice_date >= date_from)
#     if date_to:
#         q = q.filter(AccPurchaseInvoice.invoice_date <= date_to)

#     q = q.order_by(AccPurchaseInvoice.invoice_date.desc())
#     pagination = q.paginate(page=page, per_page=per_page, error_out=False)

#     columns = [
#         {"field": "name",        "label": "Bill No",     "visible": True},
#         {"field": "vendor_name", "label": "Vendor",      "visible": True},
#         {"field": "date",        "label": "Date",        "visible": True},
#         {"field": "total",       "label": "Total",       "visible": True},
#         {"field": "state",       "label": "State",       "visible": True},
#     ]

#     return render_template(
#         "erp/acc/ab_list.html",
#         items=pagination.items,
#         pagination=pagination,
#         columns=columns,
#         doctype="acc_purchase_invoice",
#         title="Purchase Invoices",
#         new_url="/admin/erp/acc/purchase-invoice/add/",
#         reports=[],
#         filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
#         main_title="Purchase Invoices",
#     )


# # ── TASK 2d: Journal Entries list ─────────────────────────────────────────────

# @app_bp.route("/acc/journal-entries/")
# @login_required
# def journal_entries_list():
#     from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournal

#     search    = request.args.get("search", "")
#     state     = request.args.get("state", "")
#     date_from = request.args.get("date_from", "")
#     date_to   = request.args.get("date_to", "")
#     page      = int(request.args.get("page", 1))
#     per_page  = int(request.args.get("per_page", 20))

#     q = AccJournalEntry.query
#     if search:
#         q = q.filter(
#             db.or_(
#                 AccJournalEntry.name.ilike(f"%{search}%"),
#                 AccJournalEntry.reference.ilike(f"%{search}%"),
#             )
#         )
#     if state:
#         q = q.filter(AccJournalEntry.state == state)
#     if date_from:
#         q = q.filter(AccJournalEntry.date_entry >= date_from)
#     if date_to:
#         q = q.filter(AccJournalEntry.date_entry <= date_to)

#     q = q.order_by(AccJournalEntry.date_entry.desc())
#     pagination = q.paginate(page=page, per_page=per_page, error_out=False)

#     columns = [
#         {"field": "name",         "label": "Entry No",    "visible": True},
#         {"field": "date_entry",   "label": "Date",        "visible": True},
#         {"field": "journal",      "label": "Journal",     "visible": True},
#         {"field": "state",        "label": "State",       "visible": True},
#         {"field": "amount_total", "label": "Amount",      "visible": True},
#     ]

#     return render_template(
#         "erp/acc/journal_entries_list.html",
#         items=pagination.items,
#         pagination=pagination,
#         columns=columns,
#         doctype="acc_journal_entry",
#         title="Journal Entries",
#         new_url="/admin/erp/acc/entry/add/",
#         reports=[],
#         filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
#         main_title="Journal Entries",
#     )


# ── TASK 3b: POS Shift Report ─────────────────────────────────────────────────

@app_bp.route("/reports/pos-shift/")
@login_required
def pos_shift_report():
    date_from  = request.args.get("date_from", "")
    date_to    = request.args.get("date_to", "")
    page       = int(request.args.get("page", 1))
    per_page   = int(request.args.get("per_page", 20))

    sql = """
        SELECT
          ps.id,
          ps.shift_number,
          u.username  AS cashier,
          pt.name     AS terminal,
          ps.opened_at,
          ps.closed_at,
          ps.state,
          COUNT(po.id)                   AS total_orders,
          COALESCE(SUM(po.total), 0)     AS total_sales,
          ps.opening_balance,
          ps.closing_balance,
          ps.cash_difference
        FROM pos_session ps
        JOIN auth_users u  ON u.id  = ps.cashier_id
        JOIN pos_terminal pt ON pt.id = ps.terminal_id
        LEFT JOIN pos_order po ON po.session_id = ps.id AND po.state IN ('paid','invoiced')
        WHERE 1=1
    """
    params = {}
    if date_from:
        sql += " AND DATE(ps.opened_at) >= :date_from"
        params["date_from"] = date_from
    if date_to:
        sql += " AND DATE(ps.opened_at) <= :date_to"
        params["date_to"] = date_to
    sql += " GROUP BY ps.id ORDER BY ps.opened_at DESC"

    count_sql = f"SELECT COUNT(*) FROM ({sql}) AS sub"
    total = db.session.execute(db.text(count_sql), params).scalar() or 0

    offset = (page - 1) * per_page
    sql += f" LIMIT {per_page} OFFSET {offset}"
    rows = db.session.execute(db.text(sql), params).fetchall()

    class FakePagination:
        def __init__(self, total, page, per_page):
            self.total = total
            self.page  = page
            self.per_page = per_page
            self.pages = max(1, (total + per_page - 1) // per_page)
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1
            self.next_num = page + 1
            self.iter_pages = lambda **kw: range(1, self.pages + 1)

    pagination = FakePagination(total, page, per_page)

    return render_template(
        "erp/reports/pos_shift.html",
        rows=rows,
        pagination=pagination,
        filters={"date_from": date_from, "date_to": date_to},
        main_title="POS Shift Report",
    )


# ── List-view user setting API ────────────────────────────────────────────────

@app_bp.route("/api/list-setting/", methods=["POST"])
@login_required
def api_save_list_setting():
    from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
    data = request.get_json() or {}
    doctype = data.get("doctype")
    if not doctype:
        return jsonify({"ok": False, "error": "doctype required"}), 400

    setting = ErpListViewSetting.query.filter_by(
        user_id=current_user.id, doctype=doctype
    ).first()
    if not setting:
        setting = ErpListViewSetting(user_id=current_user.id, doctype=doctype)
        db.session.add(setting)

    if "page_size" in data:
        setting.page_size = int(data["page_size"])
    if "view_mode" in data:
        setting.view_mode = data["view_mode"]
    if "show_totals" in data:
        setting.show_totals = bool(data["show_totals"])
    db.session.commit()
    return jsonify({"ok": True})


# ── Report setting API ────────────────────────────────────────────────────────

@app_bp.route("/api/report-setting/<int:report_id>/", methods=["GET", "POST"])
@login_required
def api_report_setting(report_id):
    from aras.app_erp.erp_core.models.list_view import ErpReportSetting
    if request.method == "GET":
        s = ErpReportSetting.query.filter_by(
            user_id=current_user.id, report_id=report_id
        ).first()
        if not s:
            return jsonify({"date_preset": "this_month", "date_from": None, "date_to": None,
                            "params_json": None, "per_page": 50})
        return jsonify({
            "date_preset": s.date_preset,
            "date_from": s.date_from,
            "date_to": s.date_to,
            "params_json": s.params_json,
            "per_page": s.per_page,
        })

    data = request.get_json() or {}
    s = ErpReportSetting.query.filter_by(
        user_id=current_user.id, report_id=report_id
    ).first()
    if not s:
        s = ErpReportSetting(user_id=current_user.id, report_id=report_id)
        db.session.add(s)
    if "date_preset" in data:   s.date_preset  = data["date_preset"]
    if "date_from"   in data:   s.date_from    = data["date_from"]
    if "date_to"     in data:   s.date_to      = data["date_to"]
    if "params_json" in data:   s.params_json  = json.dumps(data["params_json"])
    if "per_page"    in data:   s.per_page     = int(data["per_page"])
    db.session.commit()
    return jsonify({"ok": True})


# ── Report browser ────────────────────────────────────────────────────────────

@app_bp.route("/reports/")
@login_required
def reports_index():
    from aras.app_erp.erp_core.models.report import ErpReport
    from aras.app_erp.erp_core.models.list_view import ErpReportSetting
    reports = ErpReport.query.filter_by(is_active=True).order_by(
        ErpReport.module, ErpReport.title
    ).all()

    grouped = {}
    for r in reports:
        grouped.setdefault(r.module, []).append(r)

    # Load user's saved settings for all reports
    settings_map = {}
    saved = ErpReportSetting.query.filter_by(user_id=current_user.id).all()
    for s in saved:
        settings_map[s.report_id] = s

    # Companies for the company selector
    from aras.app_erp.erp_core.models.company import CoreCompany
    companies = CoreCompany.query.filter_by(is_active=True).order_by(CoreCompany.id).all()
    default_company_id = _get_company_id()

    return render_template(
        "erp/reports/index.html",
        grouped=grouped,
        settings_map=settings_map,
        companies=companies,
        default_company_id=default_company_id,
        main_title="Reports",
    )


@app_bp.route("/reports/<int:report_id>/")
@login_required
def report_run(report_id):
    from aras.app_erp.erp_core.models.report import ErpReport
    from aras.app_erp.erp_core.services.report_runner import run_report

    report = ErpReport.query.get_or_404(report_id)
    filters_def = json.loads(report.filters_json) if report.filters_json else []

    if report.render_mode == "list":
        # Always run immediately; filters come from query params
        filters = {}
        for f in filters_def:
            val = request.args.get(f["field"], "")
            filters[f["field"]] = val if val else None
        result = run_report(report_id, filters, _get_company_id())
        columns = result.get("columns", [])
        rows = result.get("data", [])
        error = result.get("error")

        # Build per-column filter state for the panel
        active_filters = []
        for k, v in request.args.items():
            if k.startswith("f_col") or k.startswith("f_op") or k.startswith("f_val"):
                pass  # handled below
        f_cols = request.args.getlist("f_col[]")
        f_ops  = request.args.getlist("f_op[]")
        f_vals = request.args.getlist("f_val[]")
        active_filters = [
            {"col": c, "op": o, "val": v}
            for c, o, v in zip(f_cols, f_ops, f_vals)
        ]

        # Apply client-side column filters to rows
        def _apply_filters(rows, columns, active_filters):
            if not active_filters:
                return rows
            col_idx = {c["field"]: i for i, c in enumerate(columns)}
            out = []
            for row in rows:
                match = True
                for af in active_filters:
                    idx = col_idx.get(af["col"])
                    if idx is None:
                        continue
                    cell = str(row[idx] if row[idx] is not None else "").lower()
                    val  = af["val"].lower()
                    op   = af["op"]
                    if op == "equals" and cell != val:
                        match = False; break
                    elif op == "not_equals" and cell == val:
                        match = False; break
                    elif op == "like" and val not in cell:
                        match = False; break
                    elif op == "not_like" and val in cell:
                        match = False; break
                    elif op == "is" and cell != "":
                        match = False; break
                if match:
                    out.append(row)
            return out

        rows = _apply_filters(rows, columns, active_filters)

        search_q = request.args.get("q", "").strip()
        if search_q:
            sq = search_q.lower()
            rows = [r for r in rows if any(sq in str(v).lower() for v in r if v is not None)]

        return render_template(
            "erp/reports/run_list.html",
            report=report,
            filters_def=filters_def,
            filters=filters,
            columns=columns,
            rows=rows,
            error=error,
            active_filters=active_filters,
            search_q=search_q,
            main_title=report.title,
        )

    # custom render mode — filter-gate, script/formula view
    filters = {}
    for f in filters_def:
        val = request.args.get(f["field"], "")
        filters[f["field"]] = val if val else None

    result = None
    if request.args:
        result = run_report(report_id, filters, _get_company_id())

    return render_template(
        "erp/reports/run.html",
        report=report,
        filters_def=filters_def,
        filters=filters,
        result=result,
        main_title=report.title,
    )


@app_bp.route("/reports/<int:report_id>/run/")
@login_required
def report_run_custom(report_id):
    """Always renders the custom/formula view (run.html), ignoring render_mode."""
    from aras.app_erp.erp_core.models.report import ErpReport
    from aras.app_erp.erp_core.services.report_runner import run_report

    report = ErpReport.query.get_or_404(report_id)
    filters_def = json.loads(report.filters_json) if report.filters_json else []

    filters = {}
    for f in filters_def:
        val = request.args.get(f["field"], "")
        filters[f["field"]] = val if val else None

    result = None
    if request.args:
        result = run_report(report_id, filters, _get_company_id())

    return render_template(
        "erp/reports/run.html",
        report=report,
        filters_def=filters_def,
        filters=filters,
        result=result,
        main_title=report.title,
    )


@app_bp.route("/reports/<int:report_id>/meta.json")
@login_required
def report_meta_json(report_id):
    """Return report metadata (title, filters_def, columns, render_mode) for the index panel."""
    from aras.app_erp.erp_core.models.report import ErpReport
    report = ErpReport.query.get_or_404(report_id)
    filters_def = json.loads(report.filters_json) if report.filters_json else []
    columns = json.loads(report.columns_json) if report.columns_json else []
    return jsonify({
        "id": report.id,
        "name": report.name,
        "title": report.title,
        "report_type": report.report_type,
        "render_mode": report.render_mode,
        "filters_def": filters_def,
        "columns": columns,
    })


@app_bp.route("/reports/<int:report_id>/data.json")
@login_required
def report_data_json(report_id):
    from aras.app_erp.erp_core.services.report_runner import run_report

    filters = {}
    for k, v in request.args.items():
        if k != "company_id":
            filters[k] = v if v else None

    # Allow overriding company_id via param (from index panel company selector)
    company_id = request.args.get("company_id", type=int) or _get_company_id()
    result = run_report(report_id, filters, company_id)
    return jsonify(result)


@app_bp.route("/reports/<int:report_id>/export.csv")
@login_required
def report_export_csv(report_id):
    from aras.app_erp.erp_core.models.report import ErpReport
    from aras.app_erp.erp_core.services.report_runner import run_report

    report = ErpReport.query.get_or_404(report_id)
    filters = {}
    for k, v in request.args.items():
        filters[k] = v if v else None

    result = run_report(report_id, filters, _get_company_id())

    output = io.StringIO()
    writer = csv.writer(output)
    cols = result.get("columns", [])
    writer.writerow([c.get("label", c.get("field", "")) for c in cols])
    for row in result.get("data", []):
        writer.writerow(row)

    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={report.name}.csv"},
    )
