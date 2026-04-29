import json
import csv
import io
from flask import render_template, request, jsonify, redirect, url_for, flash, Response, current_app
from flask_login import login_required, current_user
from . import app_bp
from arasCore.lib.core.extensions import db


def _get_company_id():
    from aras.erp.erp_core.models.company import Company
    cid = getattr(current_user, "company_id", None)
    if not cid:
        company = Company.query.filter_by(is_active=True).order_by(Company.id).first()  # needs order_by
        cid = company.id if company else None
    return cid


# # ── TASK 1: Journal Entry detail ─────────────────────────────────────────────

# @app_bp.route("/acc/entry/<int:item_id>/")
# @login_required
# def journal_entry_detail(item_id):
#     from aras.erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
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
#     from aras.erp.erp_core.models.list_view import ErpListViewSetting
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
#     from aras.erp.erp_core.models.list_view import ErpListViewSetting
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
#     from aras.erp.erp_acc.models.invoice import AccSalesInvoice
#     from aras.erp.erp_crm.models.customer import CrmCustomer

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
#     from aras.erp.erp_acc.models.invoice import AccPurchaseInvoice

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
#     from aras.erp.erp_acc.models.journal import AccJournalEntry, AccJournal

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


# ── TASK 3b: POS Shift Report (Handled by dynamic reports) ────────────────────

# ── List-view user setting API ────────────────────────────────────────────────

@app_bp.route("/api/list-setting/", methods=["POST"])
@login_required
def api_save_list_setting():
    from aras.erp.erp_core.models.list_view import ErpListViewSetting
    data = request.get_json() or {}
    doctype = data.get("doctype")
    if not doctype:
        return jsonify({"ok": False, "error": "doctype required"}), 400

    setting, _ = ErpListViewSetting.get_or_create(
        {}, user_id=current_user.id, doctype=doctype
    )
    updates = {}
    if "page_size"   in data: updates["page_size"]   = int(data["page_size"])
    if "view_mode"   in data: updates["view_mode"]   = data["view_mode"]
    if "show_totals" in data: updates["show_totals"] = bool(data["show_totals"])
    if updates:
        setting.update_self(updates)
    return jsonify({"ok": True})


# ── Report setting API ────────────────────────────────────────────────────────

@app_bp.route("/api/report-setting/<int:report_id>/", methods=["GET", "POST"])
@login_required
def api_report_setting(report_id):
    from aras.erp.erp_core.models.list_view import ErpReportSetting
    if request.method == "GET":
        s = ErpReportSetting.find(user_id=current_user.id, report_id=report_id)
        if not s:
            return jsonify({"date_preset": "this_month", "date_from": None, "date_to": None,
                            "params_json": None, "per_page": 50})
        return jsonify({"date_preset": s.date_preset, "date_from": s.date_from,
                        "date_to": s.date_to, "params_json": s.params_json, "per_page": s.per_page})

    data = request.get_json() or {}
    s, _ = ErpReportSetting.get_or_create({}, user_id=current_user.id, report_id=report_id)
    updates = {}
    if "date_preset" in data: updates["date_preset"] = data["date_preset"]
    if "date_from"   in data: updates["date_from"]   = data["date_from"]
    if "date_to"     in data: updates["date_to"]     = data["date_to"]
    if "params_json" in data: updates["params_json"] = json.dumps(data["params_json"])
    if "per_page"    in data: updates["per_page"]    = int(data["per_page"])
    if updates:
        s.update_self(updates)
    return jsonify({"ok": True})


# ── Report browser ────────────────────────────────────────────────────────────

@app_bp.route("/reports/")
@login_required
def reports_index():
    from aras.erp.erp_core.models.report import ErpReport
    from aras.erp.erp_core.models.list_view import ErpReportSetting
    reports = ErpReport.query.filter_by(is_active=True).order_by(
        ErpReport.module, ErpReport.title
    ).all()

    grouped = {}
    for r in reports:
        grouped.setdefault(r.module, []).append(r)

    # Load user's saved settings for all reports
    settings_map = {}
    saved = ErpReportSetting.find_all(user_id=current_user.id)
    for s in saved:
        settings_map[s.report_id] = s

    # Companies for the company selector
    from aras.erp.erp_core.models.company import Company
    companies = Company.query.filter_by(is_active=True).order_by(Company.id).all()
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
    from aras.erp.erp_core.models.report import ErpReport
    from aras.erp.erp_core.services.report_runner import run_report
    from jinja2.exceptions import TemplateNotFound

    report = ErpReport.get_or_404(report_id)
    filters_def = json.loads(report.filters_json) if report.filters_json else []
    
    # Check for custom template
    template_name = "erp/reports/run.html"
    custom_tpl = f"erp/reports/custom/{report.name}.html"
    try:
        current_app.jinja_env.get_template(custom_tpl)
        template_name = custom_tpl
    except TemplateNotFound:
        pass

    filters = {}
    for f in filters_def:
        val = request.args.get(f["field"], "")
        filters[f["field"]] = val if val else None
    
    result = run_report(report_id, filters, _get_company_id())
    columns = result.get("columns", [])
    rows = result.get("data", [])
    error = result.get("error")

    return render_template(
        template_name,
        report=report,
        filters_def=filters_def,
        filters=filters,
        columns=columns,
        rows=rows,
        error=error,
        main_title=report.title,
        **result
    )


@app_bp.route("/reports/<int:report_id>/meta.json")
@login_required
def report_meta_json(report_id):
    """Return report metadata (title, filters_def, columns, render_mode) for the index panel."""
    from aras.erp.erp_core.models.report import ErpReport
    report = ErpReport.get_or_404(report_id)
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
    from aras.erp.erp_core.models.report import ErpReport
    from aras.erp.erp_core.services.report_runner import run_report
    from jinja2.exceptions import TemplateNotFound

    report = ErpReport.get_or_404(report_id)
    filters = {}
    for k, v in request.args.items():
        if k != "company_id":
            filters[k] = v if v else None

    company_id = request.args.get("company_id", type=int) or _get_company_id()
    result = run_report(report_id, filters, company_id)

    # Check for custom partial template (view inside index)
    partial_tpl = f"erp/reports/custom/{report.name}_partial.html"
    try:
        current_app.jinja_env.get_template(partial_tpl)
        result["html"] = render_template(partial_tpl, report=report, filters=filters, **result)
    except TemplateNotFound:
        pass

    return jsonify(result)


@app_bp.route("/reports/<int:report_id>/export.csv")
@login_required
def report_export_csv(report_id):
    from aras.erp.erp_core.models.report import ErpReport
    from aras.erp.erp_core.services.report_runner import run_report

    report = ErpReport.get_or_404(report_id)
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
