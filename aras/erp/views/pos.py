from decimal import Decimal
from flask import render_template, redirect, url_for, request, jsonify, flash, Response
from flask_login import login_required, current_user
from arasCore.lib.core.extensions import db
from . import app_bp
from aras.erp.erp_pos.models import PosTerminal, PosSession
from aras.erp.erp_stock.models import StockProduct
from aras.erp.erp_crm.models import CrmCustomer


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
        from aras.erp.erp_pos.services.order_service import open_session
        session = open_session(terminal_id, current_user.id, opening)
        # Record opening float shift entry
        from aras.erp.erp_pos.services.shift_service import record_shift_entry
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

    from aras.erp.erp_stock.services.price_service import get_price
    selling_pricelist_id  = session.terminal.selling_pricelist_id if session.terminal else None
    purchase_pricelist_id = session.terminal.purchase_pricelist_id if session.terminal else None

    for p in products:
        # Determine effective UOM for sales price
        effective_sales_uom_id = p.uom_sales_id or p.uom_id
        if effective_sales_uom_id:
            p.sales_price = float(get_price(p.id, effective_sales_uom_id, Decimal("1"), selling_pricelist_id, price_type="sales"))
        else:
            p.sales_price = 0.0

        # Determine effective UOM for purchase price
        effective_purchase_uom_id = p.uom_purchase_id or p.uom_id
        if effective_purchase_uom_id:
            p.purchase_price = float(get_price(p.id, effective_purchase_uom_id, Decimal("1"), purchase_pricelist_id, price_type="purchase"))
        else:
            p.purchase_price = 0.0

    from aras.erp.erp_core.models.company import Company
    from aras.erp.erp_core.models.currency import Currency
    company = Company.query.first()
    currency_symbol = "$"
    if company and company.base_currency_id:
        cur = Currency.query.get(company.base_currency_id)
        if cur and cur.symbol:
            currency_symbol = cur.symbol

    customers = CrmCustomer.query.order_by(CrmCustomer.name).all()
    from aras.erp.erp_sup.models.supplier import SupSupplier
    suppliers = SupSupplier.query.order_by(SupSupplier.name).all()

    # Tax/charge info for frontend price-inclusive calculation
    tax_rate   = 0.0
    tax_inclusive = False
    if company and company.default_charge_enable and company.default_charge_id:
        from aras.erp.erp_core.models.tax import Charge
        charge = Charge.query.get(company.default_charge_id)
        if charge:
            tax_rate      = float(charge.rate or 0)
            tax_inclusive = bool(charge.is_inclusive)

    return render_template(
        "erp/erp_pos_session.html",
        session=session,
        terminal=session.terminal,
        products=products,
        customers=customers,
        suppliers=suppliers,
        currency_symbol=currency_symbol,
        tax_rate=tax_rate,
        tax_inclusive=tax_inclusive,
        main_title="POS",
    )


@app_bp.route("/pos/session/<int:session_id>/close", methods=["GET", "POST"])
@login_required
def pos_close_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if request.method == "POST":
        cash_counted = Decimal(request.form.get("cash_counted", "0") or "0")
        notes = request.form.get("notes", "")
        from aras.erp.erp_pos.services.order_service import close_session
        close_session(session.id, cash_counted, notes)
        # Record closing entry
        from aras.erp.erp_pos.services.shift_service import record_shift_entry
        record_shift_entry(session.id, "closing", cash_counted,
                           note="Closing count", user_id=current_user.id)
        db.session.commit()
        flash("Sesi POS ditutup.", "success")
        return redirect(url_for("erp_views.pos_session_shift_report", session_id=session.id))
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    order_count = AccSalesInvoice.query.filter_by(pos_session_id=session_id).count()
    return render_template("erp/erp_pos_close_session.html", session=session,
                           order_count=order_count, main_title="Close Session")


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

    from aras.erp.erp_pos.services.shift_service import record_shift_entry
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
    from aras.erp.erp_pos.services.shift_service import get_shift_report
    data = get_shift_report(session_id)
    return render_template("erp/reports/custom/pos_session_shift.html", main_title="Shift Report", **data)


# ── Print / Export ────────────────────────────────────────────────────────────

@app_bp.route("/pos/invoice/<int:invoice_id>/receipt")
@login_required
def pos_receipt_html(invoice_id):
    """Return styled HTML receipt (browser print view)."""
    from aras.erp.erp_pos.services.print_service import render_receipt_html, _get_print_template
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    tpl = _get_print_template("pos.receipt", inv.company_id) if inv.company_id else None
    html = render_receipt_html(invoice_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    return Response(html, mimetype="text/html")


@app_bp.route("/pos/invoice/<int:invoice_id>/receipt.pdf")
@login_required
def pos_receipt_pdf(invoice_id):
    """Download PDF receipt via wkhtmltopdf."""
    from aras.erp.erp_pos.services.print_service import render_receipt_html, html_to_pdf, _get_print_template
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    tpl = _get_print_template("pos.receipt", inv.company_id) if inv.company_id else None
    html = render_receipt_html(invoice_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    try:
        pdf_bytes = html_to_pdf(html, paper_size="A5")
        return Response(pdf_bytes, mimetype="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="receipt-{inv.name}.pdf"'})
    except RuntimeError as e:
        flash(str(e) + " — showing HTML instead.", "warning")
        return Response(html, mimetype="text/html")


@app_bp.route("/pos/invoice/<int:invoice_id>/receipt.jpg")
@login_required
def pos_receipt_jpg(invoice_id):
    """Download JPG image of receipt via wkhtmltoimage."""
    from aras.erp.erp_pos.services.print_service import render_receipt_html, html_to_jpg, _get_print_template
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    tpl = _get_print_template("pos.receipt", inv.company_id) if inv.company_id else None
    html = render_receipt_html(invoice_id,
                               template_html=tpl.body_html if tpl else None,
                               css=tpl.css if tpl else None)
    try:
        jpg_bytes = html_to_jpg(html, width=400)
        return Response(jpg_bytes, mimetype="image/jpeg",
                        headers={"Content-Disposition": f'attachment; filename="receipt-{inv.name}.jpg"'})
    except RuntimeError as e:
        flash(str(e), "warning")
        return redirect(url_for("erp_views.pos_receipt_html", invoice_id=invoice_id))


@app_bp.route("/pos/invoice/<int:invoice_id>/print")
@login_required
def pos_invoice_print(invoice_id):
    """HTML print view for a Sales Invoice."""
    from aras.erp.erp_pos.services.print_service import render_invoice_html, _get_print_template
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
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
    from aras.erp.erp_pos.services.print_service import render_invoice_html, html_to_pdf, _get_print_template
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
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
    from aras.erp.erp_core.models.print_template import PrintTemplate
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

