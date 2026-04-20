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
    return render_template("erp/pos/home.html", terminals=terminals, main_title="arasPOT")


@app_bp.route("/pos/open/<int:terminal_id>", methods=["GET", "POST"])
@login_required
def pos_open_session(terminal_id):
    terminal = PosTerminal.query.get_or_404(terminal_id)
    existing = PosSession.query.filter_by(
        terminal_id=terminal_id, cashier_id=current_user.id, state="open"
    ).first()
    if existing:
        return redirect(url_for("erp.pos_session", session_id=existing.id))

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
        return redirect(url_for("erp.pos_session", session_id=session.id))

    return render_template("erp/pos/open_session.html", terminal=terminal, main_title="Open Session")


@app_bp.route("/pos/session/<int:session_id>")
@login_required
def pos_session(session_id):
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        flash("Sesi ini sudah ditutup.", "warning")
        return redirect(url_for("erp.pos_home"))

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
        return redirect(url_for("erp.pos_home"))
    return render_template("erp/pos/close_session.html", session=session, main_title="Close Session")


# ── API endpoints untuk POS (dipanggil via JS) ────────────────────────────────

@app_bp.route("/api/pos/products")
@login_required
def pos_api_products():
    products = (
        StockProduct.query
        .filter_by(for_sales=True, is_active=True)
        .order_by(StockProduct.name)
        .all()
    )
    return jsonify([{
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "barcode": p.barcode,
        "price": float(p.standard_price or 0),
        "uom": p.uom.name if p.uom else "",
        "type": p.product_type,
    } for p in products])


@app_bp.route("/api/pos/session/<int:session_id>/order", methods=["POST"])
@login_required
def pos_api_create_order(session_id):
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        return jsonify({"ok": False, "error": "Session closed"}), 400

    data = request.get_json() or {}
    lines_data = data.get("lines", [])
    payments_data = data.get("payments", [])
    customer_id = data.get("customer_id")

    if not lines_data:
        return jsonify({"ok": False, "error": "No items"}), 400

    subtotal = sum(float(l["subtotal"]) for l in lines_data)
    discount = float(data.get("discount_amt", 0))
    tax_amt = sum(float(l.get("tax_amt", 0)) for l in lines_data)
    total = subtotal - discount + tax_amt
    amount_paid = sum(float(p["amount"]) for p in payments_data)

    order = PosOrder(
        session_id=session_id,
        name=f"POS/{session_id}/{PosOrder.query.filter_by(session_id=session_id).count() + 1:04d}",
        customer_id=customer_id or None,
        cashier_id=current_user.id,
        subtotal=subtotal,
        discount_amt=discount,
        tax_amt=tax_amt,
        total=total,
        amount_paid=amount_paid,
        change_amt=max(0, amount_paid - total),
        state="paid" if amount_paid >= total else "draft",
        note=data.get("note", ""),
    )
    db.session.add(order)
    db.session.flush()

    for l in lines_data:
        line = PosOrderLine(
            order_id=order.id,
            product_id=l.get("product_id") or None,
            product_name=l["product_name"],
            product_code=l.get("product_code", ""),
            qty=l["qty"],
            unit_price=l["unit_price"],
            discount_pct=l.get("discount_pct", 0),
            tax_amt=l.get("tax_amt", 0),
            subtotal=l["subtotal"],
            note=l.get("note", ""),
        )
        db.session.add(line)

    for p in payments_data:
        payment = PosPayment(
            order_id=order.id,
            method=p.get("method", "cash"),
            amount=p["amount"],
            reference=p.get("reference", ""),
        )
        db.session.add(payment)

    db.session.flush()

    if order.state == "paid":
        from aras.app_erp.erp_pos.services.pos_invoice import create_invoice_from_pos
        create_invoice_from_pos(order.id)

    db.session.commit()
    return jsonify({"ok": True, "order_id": order.id, "name": order.name, "change": float(order.change_amt)})
