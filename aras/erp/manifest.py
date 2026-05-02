# -*- coding: utf-8 -*-
from arasCore.lib.services.app_helper import AppHelper, MenuGroup, ResourceDef, SubHandler, CustomRoute

# Important: Import AccAccount before core/tax models because of relationships
from aras.erp.erp_acc.models.account import AccAccount
from aras.erp.erp_acc.models import (
    AccJournalEntry, AccJournalLine,
    AccAnalyticTag,
    SalesOrder, SalesOrderLine, SalesOrderCharge,
    AccSalesInvoice, AccSalesInvoiceLine, AccSalesInvoiceCharge,
    AccPurchaseInvoice, AccPurchaseInvoiceLine, AccPurchaseInvoiceCharge,
    AccPayment, AccPaymentAllocation,
)
from aras.erp.erp_core.models.tax import Charge
from aras.erp.erp_core.models import (
    Company,
    Currency, FxRate,
    Setting, Sequence,
    FiscalYear, FiscalPeriod,
    ErpRole, ErpPermission,
    Attachment, PrintTemplate,
    ErpReport,
)
from aras.erp.erp_core.models.payment_mode import ModeOfPayment
from aras.erp.erp_crm.models import (
    CrmCustomer, CrmContact,
    CrmLead, CrmPipeline, CrmStage, CrmActivity,
)
from aras.erp.erp_sup.models import (
    SupSupplier,
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge,
)
from aras.erp.erp_pos.models import (
    PosTerminal, PosSession, PosShiftEntry,
)
from aras.erp.erp_stock.models import (
    StockUomCategory, StockUom, StockUomConversion,
    StockProductCategory, StockProduct, StockProductUom,
    StockPriceType, StockPriceList, StockProductBundle, StockProductAccountLink,
    StockPromoBundle, StockPromoBundleItem,
    StockLocation, StockProductLocation,
    StockMovement, StockMovementLine,
    DeliveryTrip, DeliveryOrder, DeliveryOrderLine,
)


class JournalEntryHandler(SubHandler):
    def list(self, query):
        return query.filter_by(state="draft")

    def before_delete(self, obj):
        if getattr(obj, "state", "draft") == "posted":
            raise ValueError("Journal entry yang sudah diposting tidak bisa dihapus.")


class CustomerHandler(SubHandler):
    def detail_context(self, obj):
        if not obj:
            return {}
        try:
            from arasCore.lib.core.extensions import db
            # AR balance = sum of debit - credit on receivable account lines for this customer
            rows = db.session.execute(db.text(
                "SELECT COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0) "
                "FROM acc_journal_line jl "
                "JOIN acc_journal_entry je ON je.id = jl.entry_id "
                "WHERE jl.partner_id = :cid AND jl.partner_type = 'customer' "
                "  AND je.state = 'posted'"
            ), {"cid": obj.id}).fetchone()
            ar_balance = float(rows[0]) if rows and rows[0] else 0.0
            invoices = db.session.execute(db.text(
                "SELECT COUNT(*), COALESCE(SUM(total),0) "
                "FROM acc_sales_invoice WHERE customer_id = :cid AND state != 'cancelled'"
            ), {"cid": obj.id}).fetchone()
            return {"sidebar_cards": [{
                "title": "AR / Customer Balance",
                "rows": [
                    {"label": "Outstanding AR", "value": f"{ar_balance:,.2f}"},
                    {"label": "Total Invoices", "value": str(invoices[0] if invoices else 0)},
                    {"label": "Invoice Total", "value": f"{float(invoices[1] if invoices else 0):,.2f}"},
                ],
            }]}
        except Exception:
            return {}


class PostableInvoiceHandler(SubHandler):
    """Handler untuk Sales/Purchase Invoice — inject post_url ke form context."""
    def __init__(self, post_url: str):
        self._post_url = post_url

    def detail_context(self, obj):
        if not obj:
            return {}
        state = getattr(obj, "state", None)

        # ── Workflow Override Logic ──
        from arasCore.lib.services.workflow import get_workflow, get_available_actions
        from flask_login import current_user

        # Map model name to resource key
        cls_name = obj.__class__.__name__
        res_key = None
        if cls_name == "AccSalesInvoice":
            res_key = "erp/acc/sales-invoice"
        elif cls_name == "AccPurchaseInvoice":
            res_key = "erp/acc/purchase-invoice"

        if res_key:
            wf = get_workflow(res_key)
            if wf:
                actions = get_available_actions(current_user, obj, wf)
                return {
                    "obj_state": state,
                    "workflow_actions": actions,
                    "workflow_resource_key": res_key,
                    "obj_id": obj.id
                }

        # ── Fallback to standard behavior ──
        if state == "draft":
            return {"post_url": self._post_url, "obj_id": obj.id}
        return {"obj_state": state}


class StockProductHandler(SubHandler):
    def detail_context(self, obj):
        if not obj:
            return {}
        try:
            from aras.erp.erp_stock.services.stock_compute import (
                compute_qty_by_location, compute_avg_cost, compute_qty
            )
            from aras.erp.erp_stock.models.warehouse import StockLocation

            loc_qtys = compute_qty_by_location(obj.id, company_id=obj.company_id)
            stock_rows = []
            for loc_id, qty in sorted(loc_qtys.items(), key=lambda x: x[0]):
                if qty == 0:
                    continue
                loc = StockLocation.get(loc_id)
                loc_name = loc.name if loc else f"Loc#{loc_id}"
                stock_rows.append({"label": loc_name, "value": f"{float(qty):,.4g}"})

            total_qty   = float(compute_qty(obj.id, company_id=obj.company_id))
            avg_cost    = float(compute_avg_cost(obj.id, company_id=obj.company_id))
            total_value = total_qty * avg_cost

            stock_rows += [
                {"label": "─────────", "value": ""},
                {"label": "Total Qty",   "value": f"{total_qty:,.4g}"},
                {"label": "Avg Cost",    "value": f"{avg_cost:,.2f}"},
                {"label": "Total Value", "value": f"{total_value:,.2f}"},
            ]
            return {"sidebar_cards": [{"title": "Stock & Valuation", "rows": stock_rows}]}
        except Exception:
            return {}


class LeadHandler(SubHandler):
    def detail_context(self, obj):
        if not obj or obj.state == "won":
            return {}
        return {"convert_url": "/api/erp/crm/lead/convert-customer/"}


class SalesOrderHandler(SubHandler):
    def detail_context(self, obj):
        if not obj:
            return {}
        if obj.state == "confirmed":
            return {
                "post_url": "/api/erp/acc/sales-order/create-invoice/",
                "obj_id":   obj.id,
            }
        return {"obj_state": obj.state}


class PurchaseOrderHandler(SubHandler):
    def detail_context(self, obj):
        if not obj:
            return {}
        if obj.state == "confirmed":
            return {
                "post_url": "/api/erp/sup/purchase-order/create-invoice/",
                "obj_id":   obj.id,
            }
        return {"obj_state": obj.state}


def _handle_post_journal():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    entry_id = data.get("entry_id")
    if not entry_id:
        return jsonify({"ok": False, "error": "entry_id required"}), 400
    obj = AccJournalEntry.get_or_404(entry_id)
    if getattr(obj, "state", "draft") == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    obj.set_field("state", "posted")
    return jsonify({"ok": True, "data": {"id": obj.id, "state": obj.state}})



# ── arasPos Custom API Handlers ───────────────────────────────────────────────

def _pos_products(session_id: int):
    """GET /api/erp/pos/session/<id>/products — produk + harga pricelist + stok warehouse terminal."""
    from flask import jsonify, request
    from decimal import Decimal
    from aras.erp.erp_pos.models import PosSession
    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_stock.models import StockProduct
    from aras.erp.erp_stock.models.warehouse import StockLocation
    from aras.erp.erp_stock.services.price_service import get_price
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
        # include selected location + all child locations
        loc_ids = [location_id] + [
            l.id for l in StockLocation.find_all(parent_id=location_id, is_active=True)
        ]

    q = StockProduct.query.filter_by(is_active=True)
    if tx_mode == "income":
        q = q.filter_by(for_sales=True)
    elif tx_mode == "outcome":
        q = q.filter_by(for_purchase=True)
    # "both" → tampilkan semua aktif
    products = q.order_by(StockProduct.name).all()

    result = []
    for p in products:
        sales_uom    = p.uom_sales or p.uom
        sales_uom_id = sales_uom.id if sales_uom else p.uom_id
        price = float(get_price(p.id, sales_uom_id, Decimal("1"), pricelist_id)) if sales_uom_id else 0.0

        qty_on_hand = None
        if p.is_stock_item and loc_ids:
            from aras.erp.erp_stock.services.stock_compute import compute_qty
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

        # For outcome mode: use purchase UoM + purchase price
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
    """GET /api/erp/pos/session/<id>/stock/<product_id> — cek stok per produk."""
    from flask import jsonify
    from aras.erp.erp_pos.models import PosSession
    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_stock.models import StockProduct
    from aras.erp.erp_stock.models.warehouse import StockLocation
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
    from aras.erp.erp_stock.services.stock_compute import compute_qty
    from decimal import Decimal
    total = Decimal("0")
    for lid in loc_ids:
        total += compute_qty(product_id, location_id=lid)
    return jsonify({"qty_on_hand": float(total), "storable": True})


def _pos_create_order(session_id: int):
    """POST /api/erp/pos/session/<id>/order — buat order + bayar via order_service."""
    from flask import request, jsonify
    from flask_login import current_user
    from arasCore.lib.core.extensions import db
    from aras.erp.erp_pos.models import PosSession
    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_stock.models import StockProduct

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
    ui_mode       = data.get("ui_mode", "in")  # "in" or "out" from frontend toggle
    if terminal_mode == "both":
        tx_mode = "income" if ui_mode == "in" else "outcome"
    else:
        tx_mode = terminal_mode

    # Stock check only for sales (income); purchases receive stock, no check needed
    if location_id and tx_mode == "income":
        from aras.erp.erp_stock.models.warehouse import StockLocation
        from aras.erp.erp_stock.services.stock_compute import compute_qty
        from aras.erp.erp_core.models.company import Company
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
            # Resolve allow_zero_stock: product → category → company
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
        from aras.erp.erp_pos.services.order_service import create_and_pay
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


# ── Invoice: product price lookup ────────────────────────────────────────────

def _handle_product_price():
    """GET /api/erp/invoice/product-price?product_id=X&price_type_id=Y&qty=Z&price_type=sales"""
    from flask import request, jsonify
    from decimal import Decimal
    from aras.erp.erp_stock.models.product import StockProduct
    from aras.erp.erp_stock.services.price_service import get_price
    from aras.erp.erp_stock.services.coa_resolver import resolve_revenue_account, resolve_purchase_account

    product_id    = request.args.get("product_id", type=int)
    price_type_id = request.args.get("price_type_id", type=int) or request.args.get("price_list_id", type=int)
    qty           = Decimal(str(request.args.get("qty", "1")))
    price_type    = request.args.get("price_type", "sales")
    company_id    = request.args.get("company_id", type=int)


    if not product_id:
        return jsonify({"ok": False, "error": "product_id required"}), 400

    product = StockProduct.get(product_id)
    if not product:
        return jsonify({"ok": False, "error": "Product not found"}), 404

    uom_id = product.uom_sales_id if price_type == "sales" else (product.uom_purchase_id or product.uom_id)
    if not uom_id:
        uom_id = product.uom_id

    price = get_price(product_id, uom_id, qty, price_type_id, price_type)

    acc_id = None
    if company_id:
        acc_id = (resolve_revenue_account(product, company_id) if price_type == "sales"
                  else resolve_purchase_account(product, company_id))

    return jsonify({
        "ok": True,
        "product_id": product_id,
        "name": product.name,
        "description": product.name,
        "uom_id": uom_id,
        "unit_price": float(price),
        "account_id": acc_id,
    })


def _handle_bundle_promo():
    """POST /api/erp/stock/bundle-promo — check active promo bundles for cart items.
    Body: {pricelist_id: int|null, items: [{product_id, qty}]}
    Returns: {product_id: price} map for matched bundle products.
    """
    from flask import request, jsonify
    from aras.erp.erp_stock.services.promo_service import get_bundle_promo

    data          = request.get_json() or {}
    pricelist_id  = data.get("pricelist_id")
    cart_items    = data.get("items", [])

    if not cart_items:
        return jsonify({"ok": True, "prices": {}})

    try:
        prices = get_bundle_promo(cart_items, pricelist_id)
        return jsonify({"ok": True, "prices": {str(k): float(v) for k, v in prices.items()}})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Invoice: post (create journal entry from invoice) ────────────────────────

def _handle_sales_invoice_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice
    data       = request.get_json() or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return jsonify({"ok": False, "error": "invoice_id required"}), 400
    inv = AccSalesInvoice.get_or_404(invoice_id)
    if inv.state == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    try:
        from aras.erp.erp_acc.services.posting import post_sales_invoice
        post_sales_invoice(invoice_id)
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


def _handle_purchase_invoice_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    from aras.erp.erp_acc.models.invoice import AccPurchaseInvoice
    data       = request.get_json() or {}
    invoice_id = data.get("invoice_id")
    if not invoice_id:
        return jsonify({"ok": False, "error": "invoice_id required"}), 400
    inv = AccPurchaseInvoice.get_or_404(invoice_id)
    if inv.state == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    try:
        from aras.erp.erp_acc.services.purchase_posting import post_purchase_invoice
        post_purchase_invoice(invoice_id)
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Sales Order handlers ──────────────────────────────────────────────────────

def _handle_sales_order_confirm():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from aras.erp.erp_acc.services.sales_order_service import confirm_order
        confirm_order(int(order_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


def _handle_sales_order_create_invoice():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from aras.erp.erp_acc.services.sales_order_service import create_invoice_from_order
        inv = create_invoice_from_order(int(order_id))
        return jsonify({"ok": True, "invoice_id": inv.id, "invoice_name": inv.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Purchase Order handlers ───────────────────────────────────────────────────

def _handle_purchase_order_confirm():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from aras.erp.erp_sup.services.purchase_order_service import confirm_order
        confirm_order(int(order_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


def _handle_purchase_order_create_invoice():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    order_id = data.get("order_id") or data.get("obj_id")
    if not order_id:
        return jsonify({"ok": False, "error": "order_id required"}), 400
    try:
        from aras.erp.erp_sup.services.purchase_order_service import create_invoice_from_order
        inv = create_invoice_from_order(int(order_id))
        return jsonify({"ok": True, "invoice_id": inv.id, "invoice_name": inv.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Payment handlers ──────────────────────────────────────────────────────────

def _handle_payment_post():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    payment_id = data.get("payment_id") or data.get("obj_id")
    if not payment_id:
        return jsonify({"ok": False, "error": "payment_id required"}), 400
    try:
        from aras.erp.erp_acc.services.payment_service import post_payment
        post_payment(int(payment_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


def _handle_payment_allocate():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    payment_id   = data.get("payment_id")
    invoice_type = data.get("invoice_type")   # "sales" or "purchase"
    invoice_id   = data.get("invoice_id")
    amount       = data.get("amount")
    if not all([payment_id, invoice_type, invoice_id, amount]):
        return jsonify({"ok": False, "error": "payment_id, invoice_type, invoice_id, amount required"}), 400
    try:
        from aras.erp.erp_acc.services.payment_service import allocate
        alloc = allocate(int(payment_id), invoice_type, int(invoice_id), float(amount))
        return jsonify({"ok": True, "allocation_id": alloc.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── CRM lead convert handler ──────────────────────────────────────────────────

def _handle_lead_convert():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data    = request.get_json() or {}
    lead_id = data.get("lead_id") or data.get("obj_id")
    code    = data.get("customer_code")
    if not lead_id:
        return jsonify({"ok": False, "error": "lead_id required"}), 400
    try:
        from aras.erp.erp_crm.services.lead_service import convert_to_customer
        customer = convert_to_customer(int(lead_id), customer_code=code)
        return jsonify({"ok": True, "customer_id": customer.id, "customer_name": customer.name})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Delivery handlers ─────────────────────────────────────────────────────────

def _handle_delivery_assign_trip():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    delivery_id = data.get("delivery_id") or data.get("obj_id")
    trip_id     = data.get("trip_id")
    if not delivery_id or not trip_id:
        return jsonify({"ok": False, "error": "delivery_id and trip_id required"}), 400
    try:
        from aras.erp.erp_stock.services.delivery_service import assign_to_trip
        assign_to_trip(int(delivery_id), int(trip_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


def _handle_delivery_mark_delivered():
    from flask import request, jsonify
    from arasCore.lib.core.extensions import db
    data = request.get_json() or {}
    delivery_id = data.get("delivery_id") or data.get("obj_id")
    if not delivery_id:
        return jsonify({"ok": False, "error": "delivery_id required"}), 400
    try:
        from aras.erp.erp_stock.services.delivery_service import mark_delivered
        mark_delivered(int(delivery_id))
        return jsonify({"ok": True})
    except Exception as e:
        db.session.rollback()
        return jsonify({"ok": False, "error": str(e)}), 400


# ── Wrapper functions untuk CustomRoute (menerima URL args dari Flask) ────────

def _handle_pos_products(session_id):
    return _pos_products(session_id)

def _handle_pos_stock(session_id, product_id):
    return _pos_stock_check(session_id, product_id)

def _handle_pos_order(session_id):
    return _pos_create_order(session_id)


# ── Workflow Event Listeners ──────────────────────────────────────────────────

def register_erp_workflow_listeners():
    from arasCore.lib.core.events import listener
    from aras.erp.erp_acc.services.posting import post_sales_invoice
    from aras.erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from arasCore.lib.core.extensions import db

    @listener("erp/acc/sales-invoice.state_changed")
    def on_sales_invoice_state_changed(obj, to_state, **kwargs):
        if to_state == "posted":
            try:
                # obj is already updated to 'posted' state in DB, 
                # but we need to ensure journal entries are created.
                post_sales_invoice(obj.id)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

    @listener("erp/acc/purchase-invoice.state_changed")
    def on_purchase_invoice_state_changed(obj, to_state, **kwargs):
        if to_state == "posted":
            try:
                post_purchase_invoice(obj.id)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e

# Initial registration
register_erp_workflow_listeners()


def register_invoice_workflows():
    from arasCore.lib.services.workflow import WorkflowDef, TransitionDef, register_workflow
    
    # ── Sales Invoice Workflow ──
    wf_sales = WorkflowDef(
        name="Sales Invoice Workflow",
        resource_key="erp/acc/sales-invoice",
        states=["draft", "submitted", "posted", "cancelled"],
        initial="draft",
        transitions=[
            TransitionDef("submit",    "draft",     "submitted", roles=["accountant"]),
            TransitionDef("post",      "submitted", "posted",    roles=["manager"]),
            TransitionDef("cancel",    ["draft", "submitted"], "cancelled", roles=["manager"]),
        ]
    )
    register_workflow(wf_sales)

    # ── Purchase Invoice Workflow ──
    wf_pur = WorkflowDef(
        name="Purchase Invoice Workflow",
        resource_key="erp/acc/purchase-invoice",
        states=["draft", "submitted", "posted", "cancelled"],
        initial="draft",
        transitions=[
            TransitionDef("submit",    "draft",     "submitted", roles=["accountant"]),
            TransitionDef("post",      "submitted", "posted",    roles=["manager"]),
            TransitionDef("cancel",    ["draft", "submitted"], "cancelled", roles=["manager"]),
        ]
    )
    register_workflow(wf_pur)

# Register workflows
register_invoice_workflows()


helper = AppHelper(
    name="erp",
    title="ERP",
    admin_icon="fa-building",
    admin_order=5,
    menu_groups=[
        # ── Settings ────────────────────────────────────────────────────────────
        MenuGroup("Settings", "fa-cogs", order=0, resources=[
            ResourceDef("company",        Company,       admin_list=True,
                        menu_title="Company", menu_icon="fa-building-o"),
            ResourceDef("currency",       Currency,      admin_list=True,
                        menu_title="Currency", menu_icon="fa-dollar"),
            ResourceDef("fx-rate",        FxRate,        admin_list=False, is_child_table=True),
            ResourceDef("fiscal-year",    FiscalYear,    admin_list=True,
                        menu_title="Fiscal Year", menu_icon="fa-calendar"),
            ResourceDef("fiscal-period",  FiscalPeriod,  admin_list=False, is_child_table=True),
            ResourceDef("sequence",       Sequence,      admin_list=True,
                        menu_title="Sequences", menu_icon="fa-sort-numeric-asc"),
            ResourceDef("print-template", PrintTemplate, admin_list=True,
                        menu_title="Print Templates", menu_icon="fa-print"),
            ResourceDef("role",           ErpRole,          admin_list=True,
                        menu_title="Roles", menu_icon="fa-shield"),
            ResourceDef("permission",     ErpPermission,    admin_list=True,
                        menu_title="Permissions", menu_icon="fa-key"),
            ResourceDef("setting",        Setting,       admin_list=False),
            ResourceDef("attachment",     Attachment,    admin_list=False),
            # ── Reference ───────────────────────────────────────────────────────
            ResourceDef("charge",         Charge,          admin_list=True,
                        menu_title="Charges", menu_icon="fa-percent"),
            ResourceDef("payment-mode",   ModeOfPayment,   admin_list=True,
                        menu_title="Mode of Payment", menu_icon="fa-credit-card"),
        ]),

        # ── Accounting ──────────────────────────────────────────────────────────
        MenuGroup("Accounting", "fa-calculator", order=1, resources=[
            ResourceDef("acc/account",      AccAccount,       admin_list=True,
                        menu_title="Chart of Accounts", menu_icon="fa-sitemap"),
            ResourceDef("acc/entry",        AccJournalEntry,  handler=JournalEntryHandler(), admin_list=True,
                        menu_title="Journal Entries", menu_icon="fa-pencil-square-o"),
            ResourceDef("acc/line",         AccJournalLine,   admin_list=False, is_child_table=True),
            ResourceDef("acc/analytic-tag", AccAnalyticTag,   admin_list=True,
                        menu_title="Analytic Tags", menu_icon="fa-tag"),
            ResourceDef("acc/sales-order",        SalesOrder,       admin_list=True,
                        handler=SalesOrderHandler(),
                        menu_title="Sales Orders", menu_icon="fa-file-text"),
            ResourceDef("acc/sales-order-line",   SalesOrderLine,   admin_list=False, is_child_table=True),
            ResourceDef("acc/sales-order-charge", SalesOrderCharge, admin_list=False, is_child_table=True),
            ResourceDef("acc/sales-invoice",          AccSalesInvoice,        admin_list=True,
                        handler=PostableInvoiceHandler("/api/erp/acc/sales-invoice/post/"),
                        menu_title="Sales Invoices", menu_icon="fa-file-text-o"),
            ResourceDef("acc/sales-invoice-line",     AccSalesInvoiceLine,    admin_list=False, is_child_table=True),
            ResourceDef("acc/sales-invoice-charge",   AccSalesInvoiceCharge,  admin_list=False, is_child_table=True),
            ResourceDef("acc/purchase-invoice",       AccPurchaseInvoice,     admin_list=True,
                        handler=PostableInvoiceHandler("/api/erp/acc/purchase-invoice/post/"),
                        menu_title="Purchase Invoices", menu_icon="fa-file-o"),
            ResourceDef("acc/purchase-invoice-line",  AccPurchaseInvoiceLine, admin_list=False, is_child_table=True),
            ResourceDef("acc/purchase-invoice-charge",AccPurchaseInvoiceCharge,admin_list=False, is_child_table=True),
            ResourceDef("acc/payment",            AccPayment,           admin_list=True,
                        menu_title="Payments", menu_icon="fa-money"),
            ResourceDef("acc/payment-allocation", AccPaymentAllocation, admin_list=False, is_child_table=True),
        ]),

        # ── CRM ─────────────────────────────────────────────────────────────────
        MenuGroup("CRM", "fa-handshake-o", order=2, resources=[
            ResourceDef("crm/customer",  CrmCustomer,  admin_list=True,
                        handler=CustomerHandler(),
                        menu_title="Customers", menu_icon="fa-user-circle"),
            ResourceDef("crm/contact",   CrmContact,   admin_list=False, is_child_table=True),
            ResourceDef("crm/lead",      CrmLead,      admin_list=True,
                        handler=LeadHandler(),
                        menu_title="Leads", menu_icon="fa-filter"),
            ResourceDef("crm/pipeline",  CrmPipeline,  admin_list=True,
                        menu_title="Pipelines", menu_icon="fa-random"),
            ResourceDef("crm/stage",     CrmStage,     admin_list=False, is_child_table=True),
            ResourceDef("crm/activity",  CrmActivity,  admin_list=False, is_child_table=True),
        ]),

        # ── Supplier ────────────────────────────────────────────────────────────
        MenuGroup("Supplier", "fa-truck", order=3, resources=[
            ResourceDef("sup/supplier",             SupSupplier,         admin_list=True,
                        menu_title="Suppliers", menu_icon="fa-truck"),
            ResourceDef("sup/purchase-order",       PurchaseOrder,       admin_list=True,
                        handler=PurchaseOrderHandler(),
                        menu_title="Purchase Orders", menu_icon="fa-shopping-basket"),
            ResourceDef("sup/purchase-order-line",  PurchaseOrderLine,   admin_list=False, is_child_table=True),
            ResourceDef("sup/purchase-order-charge",PurchaseOrderCharge, admin_list=False, is_child_table=True),
        ]),

        # ── POS ─────────────────────────────────────────────────────────────────
        MenuGroup("arasPos", "fa-shopping-cart", order=4, resources=[
            ResourceDef("pos/open",        url="/admin/erp/pos",
                        menu_title="Open POS", menu_icon="fa-cash-register"),
            ResourceDef("pos/terminal",    PosTerminal,   admin_list=True,
                        menu_title="Terminals", menu_icon="fa-desktop"),
            ResourceDef("pos/session",     PosSession,    admin_list=True,
                        menu_title="Sessions", menu_icon="fa-clock-o"),
            ResourceDef("pos/shift-entry", PosShiftEntry, admin_list=False, is_child_table=True),
        ]),

        # ── Reports ─────────────────────────────────────────────────────────────
        MenuGroup("Reports", "fa-bar-chart", order=5, resources=[
            ResourceDef("report", ErpReport, admin_list=True,
                        menu_title="Report Templates", menu_icon="fa-file-text-o"),
        ]),

        # ── Stock ───────────────────────────────────────────────────────────────
        MenuGroup("Stock", "fa-cubes", order=6, resources=[
            ResourceDef("stock/uom-category",     StockUomCategory,     admin_list=False),
            ResourceDef("stock/uom",              StockUom,             admin_list=True,
                        menu_title="Units of Measure", menu_icon="fa-balance-scale"),
            ResourceDef("stock/uom-conversion",   StockUomConversion,   admin_list=False, is_child_table=True),
            ResourceDef("stock/product-category", StockProductCategory, admin_list=True,
                        menu_title="Product Categories", menu_icon="fa-folder-o"),
            ResourceDef("stock/product",          StockProduct,         admin_list=True,
                        menu_title="Products", menu_icon="fa-cube",
                        handler=StockProductHandler()),
            ResourceDef("stock/product-uom",      StockProductUom,      admin_list=False, is_child_table=True),
            ResourceDef("stock/product-bundle",   StockProductBundle,   admin_list=True,
                        menu_title="Product Bundles", menu_icon="fa-cubes"),
            ResourceDef("stock/product-account",  StockProductAccountLink, admin_list=False, is_child_table=True),
            ResourceDef("stock/price-type",       StockPriceType,       admin_list=True,
                        menu_title="Price Lists", menu_icon="fa-tag"),
            ResourceDef("stock/price-list-item",  StockPriceList,       admin_list=False, is_child_table=True),
            ResourceDef("stock/promo-bundle",     StockPromoBundle,     admin_list=True,
                        menu_title="Promo Bundles", menu_icon="fa-gift"),
            ResourceDef("stock/promo-bundle-item", StockPromoBundleItem, admin_list=False, is_child_table=True),
            ResourceDef("stock/location",          StockLocation,         admin_list=True,
                        menu_title="Locations", menu_icon="fa-building-o"),
            ResourceDef("stock/product-location",  StockProductLocation,  admin_list=False, is_child_table=True),
            ResourceDef("stock/movement",         StockMovement,        admin_list=True,
                        menu_title="Stock Movements", menu_icon="fa-exchange"),
            ResourceDef("stock/movement-line",    StockMovementLine,    admin_list=False, is_child_table=True),
            ResourceDef("stock/delivery-trip",    DeliveryTrip,         admin_list=True,
                        menu_title="Delivery Trips", menu_icon="fa-road"),
            ResourceDef("stock/delivery-order",   DeliveryOrder,        admin_list=True,
                        menu_title="Delivery Orders", menu_icon="fa-map-marker"),
            ResourceDef("stock/delivery-order-line", DeliveryOrderLine, admin_list=False, is_child_table=True),
        ]),
    ],
    custom_routes=[
        CustomRoute("/acc/entry/post",                          _handle_post_journal,                   methods=["POST"], require_auth=True),
        CustomRoute("/acc/sales-invoice/post",                  _handle_sales_invoice_post,             methods=["POST"], require_auth=True),
        CustomRoute("/acc/purchase-invoice/post",               _handle_purchase_invoice_post,          methods=["POST"], require_auth=True),
        CustomRoute("/acc/sales-order/confirm",                 _handle_sales_order_confirm,            methods=["POST"], require_auth=True),
        CustomRoute("/acc/sales-order/create-invoice",          _handle_sales_order_create_invoice,     methods=["POST"], require_auth=True),
        CustomRoute("/sup/purchase-order/confirm",              _handle_purchase_order_confirm,         methods=["POST"], require_auth=True),
        CustomRoute("/sup/purchase-order/create-invoice",       _handle_purchase_order_create_invoice,  methods=["POST"], require_auth=True),
        CustomRoute("/acc/payment/post",                        _handle_payment_post,                   methods=["POST"], require_auth=True),
        CustomRoute("/acc/payment/allocate",                    _handle_payment_allocate,               methods=["POST"], require_auth=True),
        CustomRoute("/crm/lead/convert-customer",               _handle_lead_convert,                   methods=["POST"], require_auth=True),
        CustomRoute("/stk/delivery/assign-trip",                _handle_delivery_assign_trip,           methods=["POST"], require_auth=True),
        CustomRoute("/stk/delivery/mark-delivered",             _handle_delivery_mark_delivered,        methods=["POST"], require_auth=True),
        CustomRoute("/invoice/product-price",                   _handle_product_price,                  methods=["GET"],  require_auth=True),
        CustomRoute("/stock/bundle-promo",                       _handle_bundle_promo,                   methods=["POST"], require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/products",   _handle_pos_products,                   methods=["GET"],  require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/stock/<int:product_id>", _handle_pos_stock,          methods=["GET"],  require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/order",      _handle_pos_order,                      methods=["POST"], require_auth=True),
    ],
    settings_schema=[
        # General
        {"key": "company_name",      "label": "Company Name",          "value_type": "string",  "default": "",     "order": 1},
        {"key": "default_currency",  "label": "Default Currency",      "value_type": "string",  "default": "IDR",  "order": 2},
        {"key": "fiscal_year_start", "label": "Fiscal Year Start (MM-DD)", "value_type": "string", "default": "01-01", "order": 3},
        {"key": "tax_inclusive",     "label": "Tax Inclusive Pricing",  "value_type": "boolean", "default": False,  "order": 4},
        {"key": "enable_multi_currency", "label": "Enable Multi-Currency", "value_type": "boolean", "default": False, "order": 5},
        {"key": "low_stock_alert",   "label": "Low Stock Alert Threshold", "value_type": "integer", "default": 10,  "order": 6},
        {"key": "report_footer",     "label": "Report Footer Text",    "value_type": "text",    "default": "",     "order": 7},
        # Global accounting defaults (overridable per product/category)
        {"key": "account_revenue_default",  "label": "Default Revenue Account (ID)",  "value_type": "integer", "default": None, "order": 8},
        {"key": "account_purchase_default", "label": "Default Purchase Account (ID)", "value_type": "integer", "default": None, "order": 9},
        {"key": "account_cogs_default",     "label": "Default COGS Account (ID)",     "value_type": "integer", "default": None, "order": 9},
        {"key": "accounting_mode_hpp",      "label": "Use COGS (HPP) Accounting Mode","value_type": "boolean", "default": False, "order": 9},
        # POS settings
        {"key": "pos_invoice_prefix",   "label": "POS Invoice Prefix",       "value_type": "string",  "default": "POS",   "order": 10},
        {"key": "pos_allow_discount",   "label": "POS Allow Discount",       "value_type": "boolean", "default": True,    "order": 11},
        {"key": "pos_print_paper",      "label": "POS Receipt Paper Size",   "value_type": "string",  "default": "A5",    "order": 12},
        {"key": "pos_receipt_width_px", "label": "POS Receipt Width (px, for JPG)", "value_type": "integer", "default": 400, "order": 13},
        {"key": "pos_cash_journal",     "label": "POS Cash Journal Code",    "value_type": "string",  "default": "CASH",  "order": 14},
        {"key": "pos_enable_shift_journal", "label": "Post Shift Entries to Journal", "value_type": "boolean", "default": True, "order": 15},
        {"key": "pos_shift_report_footer",  "label": "Shift Report Footer Text",     "value_type": "text",    "default": "",  "order": 16},
    ],
)
