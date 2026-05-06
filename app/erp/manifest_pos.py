# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_pos.models import (
    PosTerminal, PosSession, PosShiftEntry,
)

def _pos_products(session_id: int):
    from flask import jsonify, request
    from decimal import Decimal
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct
    from app.erp.erp_stock.models.warehouse import StockLocation
    from app.erp.erp_stock.services.price_service import get_price
    from arasCore.lib.core.extensions import db

    session      = PosSession.get_or_404(session_id)
    terminal     = PosTerminal.get(session.terminal_id)
    selling_pricelist_id  = terminal.selling_pricelist_id if terminal else None
    purchase_pricelist_id = terminal.purchase_pricelist_id if terminal else None
    pricelist_id = purchase_pricelist_id if (terminal and terminal.transaction_mode == 'outcome') else selling_pricelist_id
    location_id = terminal.location_id if terminal else None
    tx_mode     = terminal.transaction_mode if terminal else "income"

    loc_ids = []
    if location_id:
        loc_ids = [location_id] + [
            l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)
        ]

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
            from app.erp.erp_stock.services.stock_compute import compute_qty
            from decimal import Decimal
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

def _pos_stock_check(session_id: int, product_id: int):
    from flask import jsonify
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct
    from app.erp.erp_stock.models.warehouse import StockLocation
    from arasCore.lib.core.extensions import db

    session      = PosSession.get_or_404(session_id)
    terminal     = PosTerminal.get(session.terminal_id)
    location_id = terminal.location_id if terminal else None

    product = StockProduct.get_or_404(product_id)
    if not product.is_stock_item:
        return jsonify({"qty_on_hand": None, "storable": False})
    if not location_id:
        return jsonify({"qty_on_hand": None, "storable": True, "warning": "Location belum dikonfigurasi di terminal"})

    child_ids = [l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)]
    loc_ids   = tuple([location_id] + child_ids) or (0,)
    from app.erp.erp_stock.services.stock_compute import compute_qty
    from decimal import Decimal
    total = Decimal("0")
    for lid in loc_ids:
        total += compute_qty(product_id, location_id=lid)
    return jsonify({"qty_on_hand": float(total), "storable": True})

def _pos_create_order(session_id: int):
    from flask import request, jsonify
    from flask_login import current_user
    from arasCore.lib.core.extensions import db
    from app.erp.erp_pos.models import PosSession
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models import StockProduct

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

    terminal    = PosTerminal.get(session.terminal_id)
    location_id = terminal.location_id if terminal else None

    terminal_mode = terminal.transaction_mode if terminal else "income"
    ui_mode       = data.get("ui_mode", "in")
    if terminal_mode == "both":
        tx_mode = "income" if ui_mode == "in" else "outcome"
    else:
        tx_mode = terminal_mode

    if location_id and tx_mode == "income":
        from app.erp.erp_stock.models.warehouse import StockLocation
        from app.erp.erp_stock.services.stock_compute import compute_qty
        from app.erp.erp_core.models.company import Company
        from decimal import Decimal
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
        from app.erp.erp_pos.services.order_service import create_and_pay
        inv, change = create_and_pay(
            session_id=session_id,
            cashier_id=current_user.id,
            lines=lines_data,
            payments=payments_data,
            customer_id=customer_id,
            supplier_id=supplier_id,
            note=data.get("note", ""),
            tx_mode=tx_mode,
        )
        return jsonify({"ok": True, "invoice_id": inv.id, "name": inv.name, "change": float(change), "tx_mode": tx_mode})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400

def _handle_pos_products(session_id):
    return _pos_products(session_id)

def _handle_pos_stock(session_id, product_id):
    return _pos_stock_check(session_id, product_id)

def _handle_pos_order(session_id):
    return _pos_create_order(session_id)

menu_groups = [
    ArasGen.Menu("arasPos", "fa-shopping-cart", order=4, resources=[
        ArasGen.Resource("pos/open",        url="/admin/erp/pos",
                    menu_title="Open POS", menu_icon="fa-cash-register"),
        ArasGen.Resource("pos/terminal",    PosTerminal,   admin_list=True,
                    menu_title="Terminals", menu_icon="fa-desktop"),
        ArasGen.Resource("pos/session",     PosSession,    admin_list=True,
                    menu_title="Sessions", menu_icon="fa-clock-o"),
        ArasGen.Resource("pos/shift-entry", PosShiftEntry, admin_list=False, is_child_table=True),
    ])
]

custom_routes = [
    ArasGen.Route("/pos/session/<int:session_id>/products",   _handle_pos_products,                   methods=["GET"],  require_auth=True),
    ArasGen.Route("/pos/session/<int:session_id>/stock/<int:product_id>", _handle_pos_stock,          methods=["GET"],  require_auth=True),
    ArasGen.Route("/pos/session/<int:session_id>/order",      _handle_pos_order,                      methods=["POST"], require_auth=True),
]

settings_schema = [
    {"key": "pos_invoice_prefix",   "label": "POS Invoice Prefix",       "value_type": "string",  "default": "POS",   "order": 10},
    {"key": "pos_allow_discount",   "label": "POS Allow Discount",       "value_type": "boolean", "default": True,    "order": 11},
    {"key": "pos_print_paper",      "label": "POS Receipt Paper Size",   "value_type": "string",  "default": "A5",    "order": 12},
    {"key": "pos_receipt_width_px", "label": "POS Receipt Width (px, for JPG)", "value_type": "integer", "default": 400, "order": 13},
    {"key": "pos_cash_journal",     "label": "POS Cash Journal Code",    "value_type": "string",  "default": "CASH",  "order": 14},
    {"key": "pos_enable_shift_journal", "label": "Post Shift Entries to Journal", "value_type": "boolean", "default": True, "order": 15},
    {"key": "pos_shift_report_footer",  "label": "Shift Report Footer Text",     "value_type": "text",    "default": "",  "order": 16},
]