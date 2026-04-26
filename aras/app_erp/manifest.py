# -*- coding: utf-8 -*-
from arasCore.lib.app_helper import AppHelper, MenuGroup, ResourceDef, SubHandler, CustomRoute

from aras.app_erp.erp_core.models import (
    Company,
    Currency, FxRate,
    Charge,
    Setting, Sequence,
    FiscalYear, FiscalPeriod,
    ErpRole, ErpPermission,
    Attachment, PrintTemplate,
    ErpReport,
)
from aras.app_erp.erp_acc.models import (
    AccAccount,
    AccJournalEntry, AccJournalLine,
    AccAnalyticTag,
    AccSalesInvoice, AccSalesInvoiceLine, AccSalesInvoiceCharge,
    AccPurchaseInvoice, AccPurchaseInvoiceLine, AccPurchaseInvoiceCharge,
)
from aras.app_erp.erp_crm.models import (
    CrmCustomer, CrmContact,
    CrmLead, CrmPipeline, CrmStage, CrmActivity,
)
from aras.app_erp.erp_pos.models import (
    PosTerminal, PosSession, PosShiftEntry,
)
from aras.app_erp.erp_stock.models import (
    StockUomCategory, StockUom, StockUomConversion,
    StockProductCategory, StockProduct, StockProductUom,
    StockProductPrice, StockProductBundle, StockProductAccountLink,
    StockPriceList, StockPriceListItem,
    StockWarehouse, StockLocation,
    StockMovement, StockMovementLine, StockValuation,
)


class JournalEntryHandler(SubHandler):
    def list(self, query):
        return query.filter_by(state="draft")

    def before_delete(self, obj):
        if getattr(obj, "state", "draft") == "posted":
            raise ValueError("Journal entry yang sudah diposting tidak bisa dihapus.")


def _handle_post_journal():
    from flask import request, jsonify
    from arasCore.lib.extensions import db
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
    from aras.app_erp.erp_pos.models import PosSession
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    from aras.app_erp.erp_stock.models import StockProduct, StockValuation
    from aras.app_erp.erp_stock.models.warehouse import StockLocation
    from aras.app_erp.erp_stock.services.price_service import get_price
    from arasCore.lib.extensions import db

    session      = PosSession.get_or_404(session_id)
    terminal     = PosTerminal.get(session.terminal_id)
    pricelist_id = terminal.pricelist_id if terminal else None
    warehouse_id = terminal.warehouse_id if terminal else None
    tx_mode      = terminal.transaction_mode if terminal else "income"

    loc_ids = []
    if warehouse_id:
        loc_ids = [l.id for l in StockLocation.find_all(
            warehouse_id=warehouse_id, location_type="internal", is_active=True
        )]

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
        price = float(get_price(p.id, sales_uom_id, Decimal("1"), pricelist_id)) if sales_uom_id else float(p.standard_price or 0)

        qty_on_hand = None
        if p.product_type == "storable" and loc_ids:
            row = db.session.execute(
                db.text(
                    "SELECT COALESCE(SUM(qty_on_hand),0) FROM stock_valuation "
                    "WHERE product_id=:pid AND location_id IN :lids"
                ),
                {"pid": p.id, "lids": tuple(loc_ids)}
            ).scalar()
            qty_on_hand = float(row or 0)

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
            from aras.app_erp.erp_stock.models.pricelist import StockPriceListItem
            from datetime import date as _date
            purchase_price_row = None
            if active_uom_id:
                purchase_price_row = (
                    StockPriceListItem.query
                    .filter_by(price_list_id=pricelist_id, product_id=p.id, uom_id=active_uom_id)
                    .first() if pricelist_id else None
                )
            if purchase_price_row:
                display_price = float(purchase_price_row.price)
            else:
                display_price = float(p.cost_price or 0)
        else:
            active_uom_id = sales_uom_id
            active_uom    = sales_uom
            display_price = price

        result.append({
            "id": p.id, "code": p.code, "name": p.name, "barcode": p.barcode,
            "product_type": p.product_type,
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
    from aras.app_erp.erp_pos.models import PosSession
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    from aras.app_erp.erp_stock.models import StockProduct
    from aras.app_erp.erp_stock.models.warehouse import StockLocation
    from arasCore.lib.extensions import db

    session      = PosSession.get_or_404(session_id)
    terminal     = PosTerminal.get(session.terminal_id)
    warehouse_id = terminal.warehouse_id if terminal else None

    product = StockProduct.get_or_404(product_id)
    if product.product_type != "storable":
        return jsonify({"qty_on_hand": None, "storable": False})
    if not warehouse_id:
        return jsonify({"qty_on_hand": None, "storable": True, "warning": "Warehouse belum dikonfigurasi"})

    locs    = StockLocation.find_all(warehouse_id=warehouse_id, location_type="internal", is_active=True)
    loc_ids = tuple(l.id for l in locs) or (0,)
    qty = db.session.execute(
        db.text("SELECT COALESCE(SUM(qty_on_hand),0) FROM stock_valuation WHERE product_id=:pid AND location_id IN :lids"),
        {"pid": product_id, "lids": loc_ids}
    ).scalar()
    return jsonify({"qty_on_hand": float(qty or 0), "storable": True})


def _pos_create_order(session_id: int):
    """POST /api/erp/pos/session/<id>/order — buat order + bayar via order_service."""
    from flask import request, jsonify
    from flask_login import current_user
    from arasCore.lib.extensions import db
    from aras.app_erp.erp_pos.models import PosSession
    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    from aras.app_erp.erp_stock.models import StockProduct

    if not current_user.is_authenticated:
        return jsonify({"error": "Unauthorized"}), 401

    session = PosSession.get_or_404(session_id)
    if session.state != "open":
        return jsonify({"ok": False, "error": "Session closed"}), 400

    data          = request.get_json() or {}
    lines_data    = data.get("lines", [])
    payments_data = data.get("payments", [])
    customer_id   = data.get("customer_id") or None

    if not lines_data:
        return jsonify({"ok": False, "error": "No items"}), 400

    terminal     = PosTerminal.get(session.terminal_id)
    warehouse_id = terminal.warehouse_id if terminal else None

    if warehouse_id:
        from aras.app_erp.erp_stock.models.warehouse import StockLocation
        locs    = StockLocation.find_all(warehouse_id=warehouse_id, location_type="internal", is_active=True)
        loc_ids = tuple(l.id for l in locs) or (0,)
        for l in lines_data:
            pid = l.get("product_id")
            if not pid:
                continue
            p = StockProduct.get(pid)
            if not p or p.product_type != "storable":
                continue
            qty_base = float(l.get("qty_base") or l.get("qty", 1))
            stock = db.session.execute(
                db.text("SELECT COALESCE(SUM(qty_on_hand),0) FROM stock_valuation WHERE product_id=:pid AND location_id IN :lids"),
                {"pid": pid, "lids": loc_ids}
            ).scalar()
            if float(stock or 0) < qty_base:
                return jsonify({"ok": False, "error": f"Stok {p.name} tidak cukup (tersedia: {float(stock or 0):.2f})"}), 400

    tx_mode = terminal.transaction_mode if terminal else "income"

    try:
        from aras.app_erp.erp_pos.services.order_service import create_order, pay_order
        order = create_order(
            session_id=session_id,
            cashier_id=current_user.id,
            lines=lines_data,
            customer_id=customer_id,
            note=data.get("note", ""),
        )
        order = pay_order(order.id, payments_data, tx_mode=tx_mode)
        return jsonify({"ok": True, "order_id": order.id, "name": order.name, "change": float(order.change_amt), "tx_mode": tx_mode})
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
            ResourceDef("charge-category", admin_list=True,
                        menu_title="Charge Categories", menu_icon="fa-tags"),
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
            ResourceDef("acc/sales-invoice",          AccSalesInvoice,        admin_list=True,
                        menu_title="Sales Invoices", menu_icon="fa-file-text-o"),
            ResourceDef("acc/sales-invoice-line",     AccSalesInvoiceLine,    admin_list=False, is_child_table=True),
            ResourceDef("acc/sales-invoice-charge",   AccSalesInvoiceCharge,  admin_list=False, is_child_table=True),
            ResourceDef("acc/purchase-invoice",       AccPurchaseInvoice,     admin_list=True,
                        menu_title="Purchase Invoices", menu_icon="fa-file-o"),
            ResourceDef("acc/purchase-invoice-line",  AccPurchaseInvoiceLine, admin_list=False, is_child_table=True),
            ResourceDef("acc/purchase-invoice-charge",AccPurchaseInvoiceCharge,admin_list=False, is_child_table=True),
        ]),

        # ── CRM ─────────────────────────────────────────────────────────────────
        MenuGroup("CRM", "fa-handshake-o", order=2, resources=[
            ResourceDef("crm/customer",  CrmCustomer,  admin_list=True,
                        menu_title="Customers", menu_icon="fa-user-circle"),
            ResourceDef("crm/contact",   CrmContact,   admin_list=False, is_child_table=True),
            ResourceDef("crm/lead",      CrmLead,      admin_list=True,
                        menu_title="Leads", menu_icon="fa-filter"),
            ResourceDef("crm/pipeline",  CrmPipeline,  admin_list=True,
                        menu_title="Pipelines", menu_icon="fa-random"),
            ResourceDef("crm/stage",     CrmStage,     admin_list=False, is_child_table=True),
            ResourceDef("crm/activity",  CrmActivity,  admin_list=False, is_child_table=True),
        ]),

        # ── POS ─────────────────────────────────────────────────────────────────
        MenuGroup("arasPos", "fa-shopping-cart", order=3, resources=[
            ResourceDef("pos/open",        url="/admin/erp/pos",
                        menu_title="Open POS", menu_icon="fa-cash-register"),
            ResourceDef("pos/terminal",    PosTerminal,   admin_list=True,
                        menu_title="Terminals", menu_icon="fa-desktop"),
            ResourceDef("pos/session",     PosSession,    admin_list=True,
                        menu_title="Sessions", menu_icon="fa-clock-o"),
            ResourceDef("pos/shift-entry", PosShiftEntry, admin_list=False, is_child_table=True),
        ]),

        # ── Reports ─────────────────────────────────────────────────────────────
        MenuGroup("Reports", "fa-bar-chart", order=4, resources=[
            ResourceDef("report", ErpReport, admin_list=True,
                        menu_title="Report Templates", menu_icon="fa-file-text-o"),
        ]),

        # ── Stock ───────────────────────────────────────────────────────────────
        MenuGroup("Stock", "fa-cubes", order=5, resources=[
            ResourceDef("stock/uom-category",     StockUomCategory,     admin_list=False),
            ResourceDef("stock/uom",              StockUom,             admin_list=True,
                        menu_title="Units of Measure", menu_icon="fa-balance-scale"),
            ResourceDef("stock/uom-conversion",   StockUomConversion,   admin_list=False, is_child_table=True),
            ResourceDef("stock/product-category", StockProductCategory, admin_list=True,
                        menu_title="Product Categories", menu_icon="fa-folder-o"),
            ResourceDef("stock/product",          StockProduct,         admin_list=True,
                        menu_title="Products", menu_icon="fa-cube"),
            ResourceDef("stock/product-uom",      StockProductUom,      admin_list=False, is_child_table=True),
            ResourceDef("stock/product-price",    StockProductPrice,    admin_list=False, is_child_table=True),
            ResourceDef("stock/product-bundle",   StockProductBundle,   admin_list=True,
                        menu_title="Product Bundles", menu_icon="fa-cubes"),
            ResourceDef("stock/product-account",  StockProductAccountLink, admin_list=False, is_child_table=True),
            ResourceDef("stock/pricelist",        StockPriceList,       admin_list=True,
                        menu_title="Price Lists", menu_icon="fa-tag"),
            ResourceDef("stock/pricelist-item",   StockPriceListItem,   admin_list=False, is_child_table=True),
            ResourceDef("stock/warehouse",        StockWarehouse,       admin_list=True,
                        menu_title="Warehouses", menu_icon="fa-building-o"),
            ResourceDef("stock/location",         StockLocation,        admin_list=False, is_child_table=True),
            ResourceDef("stock/movement",         StockMovement,        admin_list=True,
                        menu_title="Stock Movements", menu_icon="fa-exchange"),
            ResourceDef("stock/movement-line",    StockMovementLine,    admin_list=False, is_child_table=True),
            ResourceDef("stock/valuation",        StockValuation,       admin_list=True,
                        menu_title="Stock Valuation", menu_icon="fa-bar-chart"),
        ]),
    ],
    custom_routes=[
        CustomRoute("/acc/entry/post",                          _handle_post_journal,    methods=["POST"], require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/products",   _handle_pos_products,    methods=["GET"],  require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/stock/<int:product_id>", _handle_pos_stock, methods=["GET"], require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/order",      _handle_pos_order,       methods=["POST"], require_auth=True),
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
