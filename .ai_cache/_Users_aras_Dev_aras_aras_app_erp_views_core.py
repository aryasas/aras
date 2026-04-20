import json
import csv
import io
from flask import render_template, request, jsonify, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from . import app_bp
from arasCore.lib.extensions import db


# ── TASK 1: Journal Entry detail ─────────────────────────────────────────────

@app_bp.route("/acc/entry/<int:item_id>/")
@login_required
def journal_entry_detail(item_id):
    from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
    entry = AccJournalEntry.query.get_or_404(item_id)
    lines = (
        AccJournalLine.query
        .filter_by(entry_id=item_id)
        .order_by(AccJournalLine.sequence)
        .all()
    )
    return render_template(
        "erp/acc/journal_entry_detail.html",
        entry=entry,
        lines=lines,
        main_title="Journal Entry",
    )


# ── TASK 2c: List-view setting API ───────────────────────────────────────────

@app_bp.route("/api/list-view-setting/", methods=["POST"])
@login_required
def api_save_list_view_setting():
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

    if "columns" in data:
        setting.columns_json = json.dumps(data["columns"])
    if "filters" in data:
        setting.filters_json = json.dumps(data["filters"])
    if "page_size" in data:
        setting.page_size = int(data["page_size"])

    db.session.commit()
    return jsonify({"ok": True})


@app_bp.route("/api/list-view-setting/<doctype>/")
@login_required
def api_get_list_view_setting(doctype):
    from aras.app_erp.erp_core.models.list_view import ErpListViewSetting
    setting = ErpListViewSetting.query.filter_by(
        user_id=current_user.id, doctype=doctype
    ).first()
    if not setting:
        return jsonify({"ok": True, "data": None})
    return jsonify({
        "ok": True,
        "data": {
            "columns":   json.loads(setting.columns_json)  if setting.columns_json  else None,
            "filters":   json.loads(setting.filters_json)  if setting.filters_json  else None,
            "page_size": setting.page_size,
        },
    })


# ── TASK 2d: Sales Invoice list ───────────────────────────────────────────────

@app_bp.route("/acc/sales-invoice/")
@login_required
def sales_invoice_list():
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice
    from aras.app_erp.erp_crm.models.customer import CrmCustomer

    search    = request.args.get("search", "")
    state     = request.args.get("state", "")
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to", "")
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 20))

    q = AccSalesInvoice.query
    if search:
        q = q.join(CrmCustomer).filter(
            db.or_(
                AccSalesInvoice.name.ilike(f"%{search}%"),
                CrmCustomer.name.ilike(f"%{search}%"),
            )
        )
    if state:
        q = q.filter(AccSalesInvoice.state == state)
    if date_from:
        q = q.filter(AccSalesInvoice.invoice_date >= date_from)
    if date_to:
        q = q.filter(AccSalesInvoice.invoice_date <= date_to)

    q = q.order_by(AccSalesInvoice.invoice_date.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    columns = [
        {"field": "name",     "label": "Invoice No", "visible": True},
        {"field": "customer", "label": "Customer",   "visible": True},
        {"field": "date",     "label": "Date",       "visible": True},
        {"field": "total",    "label": "Total",      "visible": True},
        {"field": "state",    "label": "State",      "visible": True},
    ]

    return render_template(
        "erp/acc/sales_invoice_list.html",
        items=pagination.items,
        pagination=pagination,
        columns=columns,
        doctype="acc_sales_invoice",
        title="Sales Invoices",
        new_url="/admin/erp/acc/sales-invoice/add/",
        reports=[],
        filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
        main_title="Sales Invoices",
    )


# ── TASK 2d: Purchase Invoice list ────────────────────────────────────────────

@app_bp.route("/acc/purchase-invoice/")
@login_required
def purchase_invoice_list():
    from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice

    search    = request.args.get("search", "")
    state     = request.args.get("state", "")
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to", "")
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 20))

    q = AccPurchaseInvoice.query
    if search:
        q = q.filter(
            db.or_(
                AccPurchaseInvoice.name.ilike(f"%{search}%"),
                AccPurchaseInvoice.vendor_name.ilike(f"%{search}%"),
            )
        )
    if state:
        q = q.filter(AccPurchaseInvoice.state == state)
    if date_from:
        q = q.filter(AccPurchaseInvoice.invoice_date >= date_from)
    if date_to:
        q = q.filter(AccPurchaseInvoice.invoice_date <= date_to)

    q = q.order_by(AccPurchaseInvoice.invoice_date.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    columns = [
        {"field": "name",        "label": "Bill No",     "visible": True},
        {"field": "vendor_name", "label": "Vendor",      "visible": True},
        {"field": "date",        "label": "Date",        "visible": True},
        {"field": "total",       "label": "Total",       "visible": True},
        {"field": "state",       "label": "State",       "visible": True},
    ]

    return render_template(
        "erp/acc/purchase_invoice_list.html",
        items=pagination.items,
        pagination=pagination,
        columns=columns,
        doctype="acc_purchase_invoice",
        title="Purchase Invoices",
        new_url="/admin/erp/acc/purchase-invoice/add/",
        reports=[],
        filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
        main_title="Purchase Invoices",
    )


# ── TASK 2d: Journal Entries list ─────────────────────────────────────────────

@app_bp.route("/acc/journal-entries/")
@login_required
def journal_entries_list():
    from aras.app_erp.erp_acc.models.journal import AccJournalEntry, AccJournal

    search    = request.args.get("search", "")
    state     = request.args.get("state", "")
    date_from = request.args.get("date_from", "")
    date_to   = request.args.get("date_to", "")
    page      = int(request.args.get("page", 1))
    per_page  = int(request.args.get("per_page", 20))

    q = AccJournalEntry.query
    if search:
        q = q.filter(
            db.or_(
                AccJournalEntry.name.ilike(f"%{search}%"),
                AccJournalEntry.reference.ilike(f"%{search}%"),
            )
        )
    if state:
        q = q.filter(AccJournalEntry.state == state)
    if date_from:
        q = q.filter(AccJournalEntry.date_entry >= date_from)
    if date_to:
        q = q.filter(AccJournalEntry.date_entry <= date_to)

    q = q.order_by(AccJournalEntry.date_entry.desc())
    pagination = q.paginate(page=page, per_page=per_page, error_out=False)

    columns = [
        {"field": "name",         "label": "Entry No",    "visible": True},
        {"field": "date_entry",   "label": "Date",        "visible": True},
        {"field": "journal",      "label": "Journal",     "visible": True},
        {"field": "state",        "label": "State",       "visible": True},
        {"field": "amount_total", "label": "Amount",      "visible": True},
    ]

    return render_template(
        "erp/acc/journal_entries_list.html",
        items=pagination.items,
        pagination=pagination,
        columns=columns,
        doctype="acc_journal_entry",
        title="Journal Entries",
        new_url="/admin/erp/acc/entry/add/",
        reports=[],
        filters={"search": search, "state": state, "date_from": date_from, "date_to": date_to},
        main_title="Journal Entries",
    )


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


# ── TASK 4: Report browser & runner ──────────────────────────────────────────

@app_bp.route("/reports/")
@login_required
def reports_index():
    from aras.app_erp.erp_core.models.report import ErpReport
    reports = ErpReport.query.filter_by(is_active=True).order_by(
        ErpReport.module, ErpReport.title
    ).all()

    grouped = {}
    for r in reports:
        grouped.setdefault(r.module, []).append(r)

    return render_template(
        "erp/reports/index.html",
        grouped=grouped,
        main_title="Reports",
    )


@app_bp.route("/reports/<int:report_id>/")
@login_required
def report_run(report_id):
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
        company_id = getattr(current_user, "company_id", None)
        result = run_report(report_id, filters, company_id)

    return render_template(
        "erp/reports/run.html",
        report=report,
        filters_def=filters_def,
        filters=filters,
        result=result,
        main_title=report.title,
    )


@app_bp.route("/reports/<int:report_id>/data.json")
@login_required
def report_data_json(report_id):
    from aras.app_erp.erp_core.services.report_runner import run_report

    filters = {}
    for k, v in request.args.items():
        filters[k] = v if v else None

    company_id = getattr(current_user, "company_id", None)
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

    company_id = getattr(current_user, "company_id", None)
    result = run_report(report_id, filters, company_id)

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


# ── Dashboard ─────────────────────────────────────────────────────────────────

@app_bp.route("/")
@app_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("erp/dashboard.html", main_title="ERP")
