from flask import render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from arasCore.lib.extensions import db
from . import app_bp
from aras.app_erp.erp_pos.models import PosTerminal, PosSession, PosOrder, PosOrderLine, PosPayment
from aras.app_erp.erp_stock.models import StockProduct
from aras.app_erp.erp_crm.models import CrmCustomer


@app_bp.route("/pos")
@login_required
def pos_home():
    terminals = PosTerminal.query.filter_by(is_active=True).all()
    open_sessions = {
        s.terminal_id: s
        for s in PosSession.query.filter_by(cashier_id=current_user.id, state="open").all()
    }
    return render_template("erp/pos/home.html", terminals=terminals, open_sessions=open_sessions, main_title="arasPos")


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
        opening = request.form.get("opening_balance", 0)
        session = PosSession(
            terminal_id=terminal_id,
            cashier_id=current_user.id,
            opening_balance=opening,
            state="open",
        )
        db.session.add(session)
        db.session.commit()
        return redirect(url_for("erp_views.pos_session", session_id=session.id))

    return render_template("erp/pos/open_session.html", terminal=terminal, main_title="Open Session")


@app_bp.route("/pos/session/<int:session_id>")
@login_required
def pos_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        flash("Sesi ini sudah ditutup.", "warning")
        return redirect(url_for("erp_views.pos_home"))

    # Products for_sales only
    products = (
        StockProduct.query
        .filter_by(for_sales=True, is_active=True)
        .order_by(StockProduct.name)
        .all()
    )
    customers = CrmCustomer.query.filter_by(is_active=True).order_by(CrmCustomer.name).all()

    return render_template(
        "erp/pos/session.html",
        session=session,
        terminal=session.terminal,
        products=products,
        customers=customers,
        main_title="POS",
    )


@app_bp.route("/pos/session/<int:session_id>/close", methods=["GET", "POST"])
@login_required
def pos_close_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if request.method == "POST":
        session.cash_counted = request.form.get("cash_counted", 0)
        session.notes = request.form.get("notes", "")
        session.state = "closed"
        from datetime import datetime
        session.closed_at = datetime.utcnow()
        db.session.commit()
        flash("Sesi POS ditutup.", "success")
        return redirect(url_for("erp_views.pos_home"))
    return render_template("erp/pos/close_session.html", session=session, main_title="Close Session")


# ── API endpoints untuk POS (dipanggil via JS) ────────────────────────────────


# ── Terminal Setup ────────────────────────────────────────────────────────────

@app_bp.route("/pos/terminal")
@login_required
def pos_terminal_list():
    terminals = PosTerminal.query.order_by(PosTerminal.name).all()
    return render_template("erp/pos/terminal_list.html", terminals=terminals, main_title="POT Terminal")


@app_bp.route("/pos/terminal/new", methods=["GET", "POST"])
@app_bp.route("/pos/terminal/<int:terminal_id>/edit", methods=["GET", "POST"])
@login_required
def pos_terminal_edit(terminal_id=None):
    from aras.app_erp.erp_stock.models import StockWarehouse
    from aras.app_erp.erp_stock.models.pricelist import StockPriceList
    from aras.app_erp.erp_acc.models import AccJournal
    from arasCore.lib.extensions import db as _db

    terminal = PosTerminal.query.get_or_404(terminal_id) if terminal_id else None
    warehouses = StockWarehouse.query.filter_by(is_active=True).order_by(StockWarehouse.name).all()
    pricelists = StockPriceList.query.filter_by(is_active=True, price_type="sales").order_by(StockPriceList.name).all()

    if request.method == "POST":
        f = request.form
        if not terminal:
            terminal = PosTerminal()
            _db.session.add(terminal)
        terminal.company_id     = int(f["company_id"])
        terminal.code           = f["code"].strip()
        terminal.name           = f["name"].strip()
        terminal.warehouse_id      = int(f["warehouse_id"]) if f.get("warehouse_id") else None
        terminal.pricelist_id      = int(f["pricelist_id"]) if f.get("pricelist_id") else None
        terminal.transaction_mode  = f.get("transaction_mode", "income")
        terminal.allow_discount = bool(f.get("allow_discount"))
        terminal.max_discount_pct = float(f.get("max_discount_pct") or 100)
        terminal.is_active      = bool(f.get("is_active"))
        terminal.receipt_header = f.get("receipt_header", "")
        terminal.receipt_footer = f.get("receipt_footer", "")
        _db.session.commit()
        flash("Terminal disimpan.", "success")
        return redirect(url_for("erp_views.pos_terminal_list"))

    from aras.app_erp.erp_core.models.company import CoreCompany
    companies = CoreCompany.query.filter_by(is_active=True).all()
    return render_template(
        "erp/pos/terminal_edit.html",
        terminal=terminal, warehouses=warehouses,
        pricelists=pricelists, companies=companies,
        main_title="Edit Terminal" if terminal_id else "Terminal Baru",
    )

