# -*- coding: utf-8 -*-
"""POS custom-route handlers — wired into manifest.py via CustomRoute."""
from decimal import Decimal
from flask import jsonify, request
from flask_login import current_user
from arasCore.lib.core.extensions import db


def pos_products(session_id: int):
    """GET /api/erp/pos/session/<id>/products — products + pricelist + warehouse stock."""
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct
    from app.erp.erp_stock.models.warehouse import StockLocation
    from app.erp.erp_stock.services.price import get_price
    from app.erp.erp_stock.services.stock_compute import compute_qty

    session  = PosSession.get_or_404(session_id)
    terminal = PosTerminal.get(session.terminal_id)
    selling_pricelist_id  = terminal.selling_pricelist_id  if terminal else None
    purchase_pricelist_id = terminal.purchase_pricelist_id if terminal else None
    pricelist_id = purchase_pricelist_id if (terminal and terminal.transaction_mode == "outcome") else selling_pricelist_id
    location_id  = terminal.location_id if terminal else None
    tx_mode      = terminal.transaction_mode if terminal else "income"

    loc_ids = []
    if location_id:
        loc_ids = [location_id] + [l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)]

    q = StockProduct.query.filter_by(is_active=True)
    if tx_mode == "income":
        q = q.filter_by(for_sales=True)
    elif tx_mode == "outcome":
        q = q.filter_by(for_purchase=True)
    products = q.order_by(StockProduct.name).all()

    result = []
    for p in products:
        sales_uom    = p.uom_sales or p.uom
        sales_uom_id = sales_uom.id if sales_uom else p.uom_id
        price = float(get_price(p.id, sales_uom_id, Decimal("1"), pricelist_id)) if sales_uom_id else 0.0

        qty_on_hand = None
        if p.is_stock_item and loc_ids:
            total = Decimal("0")
            for lid in loc_ids:
                total += compute_qty(p.id, location_id=lid, company_id=p.company_id)
            qty_on_hand = float(total)

        uom_alts = []
        for alt in (p.uom_alts or []):
            if not alt.is_active:
                continue
            alt_price = float(get_price(p.id, alt.uom_id, Decimal("1"), pricelist_id))
            uom_alts.append({
                "uom_id": alt.uom_id,
                "uom_name": alt.uom.name if alt.uom else "",
                "factor": float(alt.factor),
                "price": alt_price,
            })

        if tx_mode == "outcome":
            active_uom    = p.uom_purchase or p.uom
            active_uom_id = active_uom.id if active_uom else p.uom_id
            display_price = float(get_price(p.id, active_uom_id, Decimal("1"), purchase_pricelist_id, price_type="purchase"))
        else:
            active_uom_id = sales_uom_id
            active_uom    = sales_uom
            display_price = price

        result.append({
            "id": p.id, "code": p.code, "name": p.name,
            "is_stock_item": p.is_stock_item,
            "tx_mode": tx_mode,
            "uom_id": active_uom_id,
            "uom_name": active_uom.name if active_uom else "",
            "price": display_price,
            "qty_on_hand": qty_on_hand,
            "uom_alts": uom_alts,
        })
    return jsonify({"tx_mode": tx_mode, "products": result})


def pos_stock(session_id: int, product_id: int):
    """GET /api/erp/pos/session/<id>/stock/<product_id> — per-product stock."""
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct
    from app.erp.erp_stock.models.warehouse import StockLocation
    from app.erp.erp_stock.services.stock_compute import compute_qty

    session  = PosSession.get_or_404(session_id)
    terminal = PosTerminal.get(session.terminal_id)
    location_id = terminal.location_id if terminal else None

    product = StockProduct.get_or_404(product_id)
    if not product.is_stock_item:
        return jsonify({"qty_on_hand": None, "storable": False})
    if not location_id:
        return jsonify({"qty_on_hand": None, "storable": True, "warning": "Location belum dikonfigurasi di terminal"})

    child_ids = [l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)]
    loc_ids   = tuple([location_id] + child_ids) or (0,)
    total = Decimal("0")
    for lid in loc_ids:
        total += compute_qty(product_id, location_id=lid)
    return jsonify({"qty_on_hand": float(total), "storable": True})


def pos_order(session_id: int):
    """POST /api/erp/pos/session/<id>/order — create order + pay via order_service."""
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct
    from app.erp.erp_pos.services.order import create_and_pay

    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401
    session = PosSession.get_or_404(session_id)
    if session.state != "open":
        return jsonify({"ok": False, "error": "Session closed"}), 400

    data          = request.get_json() or {}
    lines_data    = data.get("lines", [])
    payments_data = data.get("payments", [])
    customer_id   = data.get("customer_id") or None
    supplier_id   = data.get("supplier_id") or None
    if not lines_data:
        return jsonify({"ok": False, "error": "No items"}), 400

    terminal     = PosTerminal.get(session.terminal_id)
    location_id  = terminal.location_id if terminal else None
    ui_mode      = data.get("ui_mode", "in")
    tx_mode      = "income" if ui_mode == "in" else "outcome"

    if location_id and tx_mode == "income":
        from app.erp.erp_stock.models.warehouse import StockLocation
        from app.erp.erp_stock.services.stock_compute import compute_qty
        from app.erp.erp_config.models.company import Company
        child_ids = [l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)]
        loc_ids   = tuple([location_id] + child_ids) or (0,)
        _company  = Company.get(terminal.company_id) if terminal else None
        for l in lines_data:
            pid = l.get("product_id")
            if not pid:
                continue
            p = StockProduct.get(pid)
            if not p or not getattr(p, "is_stock_item", True):
                continue
            azs = p.allow_zero_stock
            if azs is None and p.category:
                azs = p.category.allow_zero_stock
            if azs is None and _company:
                azs = _company.allow_zero_stock
            if azs:
                continue
            qty_base = float(l.get("qty_base") or l.get("qty", 1))
            stock = sum(compute_qty(pid, location_id=lid) for lid in loc_ids)
            if float(stock) < qty_base:
                return jsonify({"ok": False, "error": f"Stok {p.name} tidak cukup (tersedia: {float(stock):.2f})"}), 400

    try:
        inv, change = create_and_pay(
            session_id=session_id, cashier_id=current_user.id,
            lines=lines_data, payments=payments_data,
            customer_id=customer_id, supplier_id=supplier_id,
            note=data.get("note", ""), tx_mode=tx_mode,
        )
        return jsonify({"ok": True, "invoice_id": inv.id, "name": inv.name,
                        "change": float(change), "tx_mode": tx_mode})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400
