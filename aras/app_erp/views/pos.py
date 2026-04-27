from decimal import Decimal
from flask import render_template, redirect, url_for, request, jsonify, flash, Response
from flask_login import login_required, current_user
from arasCore.lib.extensions import db
from . import app_bp
from aras.app_erp.erp_pos.models import PosTerminal, PosSession, PosOrder
from aras.app_erp.erp_stock.models import StockProduct
from aras.app_erp.erp_crm.models import CrmCustomer


@app_bp.route("/pos/")
@login_required
def pos_home():
    terminals = PosTerminal.query.filter_by(is_active=True).all()
    open_sessions = {
        s.terminal_id: s
        for s in PosSession.query.filter_by(cashier_id=current_user.id, state="open").all()
    }
    return render_template("erp/erp_pos_home.html", terminals=terminals, open_sessions=open_sessions, main_title="arasPos")


@app_bp.route("/pos/open/<int:terminal_id>", methods=["GET", "POST"])
@login_required
def pos_open_session(terminal_id):
    terminal = PosTerminal.query.get_or_404(terminal_id)
    existing = PosSession.query.filter_by(
        terminal_id=terminal_id, cashier_id=current_user.id, state="open"
    ).first()
    if existing:
        return redirect(url_for("erp_views.pos_session", session_id=existing.id))

    if request.method == "POST":
        opening = Decimal(request.form.get("opening_balance", "0") or "0")
        from aras.app_erp.erp_pos.services.order_service import open_session
        session = open_session(terminal_id, current_user.id, opening)
        # Record opening float shift entry
        from aras.app_erp.erp_pos.services.shift_service import record_shift_entry
        if opening > 0:
            record_shift_entry(session.id, "opening", opening,
                               note="Opening float", user_id=current_user.id)
        db.session.commit()
        return redirect(url_for("erp_views.pos_session", session_id=session.id))

    return render_template("erp/erp_pos_open_session.html", terminal=terminal, main_title="Open Session")


@app_bp.route("/pos/session/<int:session_id>")
@login_required
def pos_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        flash("Sesi ini sudah ditutup.", "warning")
        return redirect(url_for("erp_views.pos_home"))

    products = (
        StockProduct.query
        .filter_by(is_active=True)
        .order_by(StockProduct.name)
        .all()
    )

    for p in products:
        sales_pr = next((pr for pr in p.prices if pr.price_type == 'sales' and pr.is_active), None)
        if not sales_pr:
            sales_pr = next((pr for pr in p.prices if pr.price_type == 'sales'), None)
        p.sales_price = float(sales_pr.price) if sales_pr else 0.0

        purch_pr = next((pr for pr in p.prices if pr.price_type == 'purchase' and pr.is_active), None)
        if not purch_pr:
            purch_pr = next((pr for pr in p.prices if pr.price_type == 'purchase'), None)
        p.purchase_price = float(purch_pr.price) if purch_pr else 0.0

    from aras.app_erp.erp_core.models.company import Company
    from aras.app_erp.erp_core.models.currency import Currency
    company = Company.query.first()
    currency_symbol = "$"
    if company and company.base_currency_id:
        cur = Currency.query.get(company.base_currency_id)
        if cur and cur.symbol:
            currency_symbol = cur.symbol

    customers = CrmCustomer.query.filter_by(is_active=True).order_by(CrmCustomer.name).all()

    return render_template(
        "erp/erp_pos_session.html",
        session=session,
        terminal=session.terminal,
        products=products,
        customers=customers,
        currency_symbol=currency_symbol,
        main_title="POS",
    )


@app_bp.route("/pos/session/<int:session_id>/close", methods=["GET", "POST"])
@login_required
def pos_close_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if request.method == "POST":
        cash_counted = Decimal(request.form.get("cash_counted", "0") or "0")
        notes = request.form.get("notes", "")
        from aras.app_erp.erp_pos.services.order_service import close_session
        close_session(session.id, cash_counted, notes)
        # Record closing entry
        from aras.app_erp.erp_pos.services.shift_service import record_shift_entry
        record_shift_entry(session.id, "closing", cash_counted,
                           note="Closing count", user_id=current_user.id)
        db.session.commit()
        flash("Sesi POS ditutup.", "success")
        return redirect(url_for("erp_views.pos_session_shift_report", session_id=session.id))
    return render_template("erp/erp_pos_close_session.html", session=session, main_title="Close Session")


# ── Cash In / Out ─────────────────────────────────────────────────────────────

@app_bp.route("/pos/session/<int:session_id>/cash-entry", methods=["POST"])
@login_required
def pos_cash_entry(session_id):
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        return jsonify({"ok": False, "error": "Session is not open"}), 400

    data       = request.get_json() or {}
    entry_type = data.get("type")  # cash_in / cash_out
    amount     = Decimal(str(data.get("amount", 0)))
    note       = data.get("note", "")

    if entry_type not in ("cash_in", "cash_out"):
        return jsonify({"ok": False, "error": "Invalid type"}), 400
    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400

    from aras.app_erp.erp_pos.services.shift_service import record_shift_entry
    try:
        entry = record_shift_entry(session.id, entry_type, amount, note, current_user.id)
        db.session.commit()
        return jsonify({"ok": True, "entry_id": entry.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Shift Report ──────────────────────────────────────────────────────────────

@app_bp.route("/pos/session/<int:session_id>/shift-report")
@login_required
def pos_session_shift_report(session_id):
    from aras.app_erp.erp_pos.services.shift_service import get_shift_report
    data = get_shift_report(session_id)
    return render_template("erp/reports/custom/pos_session_shift.html", main_title="Shift Report", **data)


# ── Print / Export ────────────────────────────────────────────────────────────

@app_bp.route("/pos/order/<int:order_id>/receipt")
@login_required
def pos_receipt_html(order_id):
    """Return styled HTML receipt (browser print view)."""
    from aras.app_erp.erp_pos.services.print_service import render_receipt_html, _get_print_template
    order = PosOrder.query.get_or_404(order_id)
    terminal = order.session.terminal if order.session else None
    company_id = terminal.company_id if terminal else None

    tpl = None
    if company_id:
        tpl = _get_print_template("pos.receipt", company_id)

    html = render_receipt_html(
        order_id,
        template_html=tpl.body_html if tpl else None,
        css=tpl.css if tpl else None,
    )
    return Response(html, mimetype="text/html")


@app_bp.route("/pos/order/<int:order_id>/receipt.pdf")
@login_required
def pos_receipt_pdf(order_id):
    """Download PDF receipt via wkhtmltopdf."""
    from aras.app_erp.erp_pos.services.print_service import render_receipt_html, html_to_pdf, _get_print_template
    order = PosOrder.query.get_or_404(order_id)
    terminal = order.session.terminal if order.session else None
    company_id = terminal.company_id if terminal else None

    tpl = _get_print_template("pos.receipt", company_id) if company_id else None
    html = render_receipt_html(order_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    try:
        pdf_bytes = html_to_pdf(html, paper_size="A5")
        return Response(pdf_bytes, mimetype="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="receipt-{order.name}.pdf"'})
    except RuntimeError as e:
        flash(str(e) + " — showing HTML instead.", "warning")
        return Response(html, mimetype="text/html")


@app_bp.route("/pos/order/<int:order_id>/receipt.jpg")
@login_required
def pos_receipt_jpg(order_id):
    """Download JPG image of receipt via wkhtmltoimage."""
    from aras.app_erp.erp_pos.services.print_service import render_receipt_html, html_to_jpg, _get_print_template
    order = PosOrder.query.get_or_404(order_id)
    terminal = order.session.terminal if order.session else None
    company_id = terminal.company_id if terminal else None

    tpl = _get_print_template("pos.receipt", company_id) if company_id else None
    html = render_receipt_html(order_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    try:
        jpg_bytes = html_to_jpg(html, width=400)
        return Response(jpg_bytes, mimetype="image/jpeg",
                        headers={"Content-Disposition": f'attachment; filename="receipt-{order.name}.jpg"'})
    except RuntimeError as e:
        flash(str(e), "warning")
        return redirect(url_for("erp_views.pos_receipt_html", order_id=order_id))


@app_bp.route("/pos/invoice/<int:invoice_id>/print")
@login_required
def pos_invoice_print(invoice_id):
    """HTML print view for a Sales Invoice."""
    from aras.app_erp.erp_pos.services.print_service import render_invoice_html, _get_print_template
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    tpl = _get_print_template("sales.invoice", inv.company_id)
    html = render_invoice_html(invoice_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    return Response(html, mimetype="text/html")


@app_bp.route("/pos/invoice/<int:invoice_id>/print.pdf")
@login_required
def pos_invoice_pdf(invoice_id):
    """PDF export for a Sales Invoice."""
    from aras.app_erp.erp_pos.services.print_service import render_invoice_html, html_to_pdf, _get_print_template
    from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    tpl = _get_print_template("sales.invoice", inv.company_id)
    html = render_invoice_html(invoice_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    try:
        pdf_bytes = html_to_pdf(html, paper_size="A4")
        return Response(pdf_bytes, mimetype="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="invoice-{inv.name}.pdf"'})
    except RuntimeError as e:
        flash(str(e) + " — showing HTML instead.", "warning")
        return Response(html, mimetype="text/html")


# ── Print Template Preview ────────────────────────────────────────────────────

@app_bp.route("/pos/print-template/<int:tpl_id>/preview", methods=["GET"])
@login_required
def pos_print_template_preview(tpl_id):
    """Preview a PrintTemplate rendered with dummy data."""
    from aras.app_erp.erp_core.models.print_template import PrintTemplate
    tpl = PrintTemplate.query.get_or_404(tpl_id)
    # Render with dummy/empty context so designer can see layout
    from jinja2 import Environment
    env = Environment(autoescape=True)
    try:
        rendered = env.from_string(tpl.body_html or "").render(
            order=None, invoice=None, company=None, lines=[], payments=[], customer=None
        )
    except Exception as e:
        rendered = f"<pre style='color:red'>Template error: {e}</pre>"
    css = tpl.css or ""
    html = f"<!DOCTYPE html><html><head><meta charset='UTF-8'><style>{css}</style></head><body>{rendered}</body></html>"
    return Response(html, mimetype="text/html")

