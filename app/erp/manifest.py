# -*- coding: utf-8 -*-
"""ERP — app-level manifest.

Models declare metadata via `class Foo(ArasGen.Model, module=Mod)`.
Service functions decorated with `@action` are auto-mounted as HTTP + CLI.

This file holds: app declaration, model imports (registration trigger),
URL-shaped CustomRoutes (POS), settings schema.
"""
from arasCore.lib.services.app_helper import AppHelper, MenuGroup, ResourceDef, CustomRoute
from arasCore.arasgen import auto_menu_groups

from app.erp import ERP  # noqa: F401  (registers app)


# ── Model imports trigger ArasModel registration (auto_menu_groups picks them up) ──
from app.erp.erp_acc.models.account import AccAccount  # noqa: F401
from app.erp.erp_acc.models import (  # noqa: F401
    AccJournalEntry, AccJournalLine,
    AccAnalyticTag,
    SalesOrder, SalesOrderLine, SalesOrderCharge,
    AccSalesInvoice, AccSalesInvoiceLine, AccSalesInvoiceCharge,
    AccPurchaseInvoice, AccPurchaseInvoiceLine, AccPurchaseInvoiceCharge,
    AccPayment, AccPaymentAllocation,
)
from app.erp.erp_config.models import (  # noqa: F401
    Company,
    Currency, FxRate,
    Charge,
    Attachment,
)
from app.erp.erp_main.models import (  # noqa: F401
    Setting, DocSeries,
    FiscalYear, FiscalPeriod,
    ErpRole, ErpPermission,
    PrintTemplate,
    ErpReport,
)
from app.erp.erp_main.models.payment_mode import ModeOfPayment  # noqa: F401
from app.erp.erp_crm.models import (  # noqa: F401
    CrmCustomer, CrmContact,
    CrmLead, CrmPipeline, CrmStage, CrmActivity,
)
from app.erp.erp_sup.models import (  # noqa: F401
    SupSupplier,
    PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge,
)
from app.erp.erp_pos.models import (  # noqa: F401
    PosTerminal, PosSession, PosShiftEntry,
)
from app.erp.erp_stock.models import (  # noqa: F401
    StockUom,
    StockProductCategory, StockProduct, StockProductUom,
    StockPriceType, StockPriceList, StockProductBundle, StockProductAccountLink,
    StockPromoBundle, StockPromoBundleItem,
    StockLocation, StockProductLocation,
    StockMovement, StockMovementLine,
    DeliveryTrip, DeliveryOrder, DeliveryOrderLine,
)

# Workflow event listeners (acc-specific, registered on import)
from app.erp.erp_acc.services import listeners as _acc_listeners  # noqa: F401

# URL-shaped POS handlers (have <int:session_id> path params, can't auto-derive)
from app.erp.erp_pos.services import handlers as pos_h


# ── Menu groups (auto-derived + arasPos launcher tile) ───────────────────────
def _build_menu_groups():
    groups = auto_menu_groups("erp")
    pos_link = ResourceDef(
        "pos/open", url="/admin/erp/pos",
        menu_title="Open POS", menu_icon="fa-cash-register",
    )
    for g in groups:
        if g.title == "arasPos":
            g.resources.insert(0, pos_link)
            break
    else:
        groups.append(MenuGroup("arasPos", "fa-shopping-cart", order=4, resources=[pos_link]))
    return groups


# ── Manifest ─────────────────────────────────────────────────────────────────
helper = AppHelper(
    name="erp",
    title="ERP",
    admin_icon="fa-building",
    admin_order=5,
    menu_groups=_build_menu_groups(),
    custom_routes=[
        # POS — URL-shaped (path params), kept as CustomRoute
        CustomRoute("/pos/session/<int:session_id>/products",                  pos_h.pos_products, methods=["GET"],  require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/stock/<int:product_id>",    pos_h.pos_stock,    methods=["GET"],  require_auth=True),
        CustomRoute("/pos/session/<int:session_id>/order",                     pos_h.pos_order,    methods=["POST"], require_auth=True),
    ],
    settings_schema=[
        {"key": "company_name",      "label": "Company Name",          "value_type": "string",  "default": "",     "order": 1},
        {"key": "default_currency",  "label": "Default Currency",      "value_type": "string",  "default": "IDR",  "order": 2},
        {"key": "fiscal_year_start", "label": "Fiscal Year Start (MM-DD)", "value_type": "string", "default": "01-01", "order": 3},
        {"key": "tax_inclusive",     "label": "Tax Inclusive Pricing",  "value_type": "boolean", "default": False,  "order": 4},
        {"key": "enable_multi_currency", "label": "Enable Multi-Currency", "value_type": "boolean", "default": False, "order": 5},
        {"key": "low_stock_alert",   "label": "Low Stock Alert Threshold", "value_type": "integer", "default": 10,  "order": 6},
        {"key": "report_footer",     "label": "Report Footer Text",    "value_type": "text",    "default": "",     "order": 7},
        {"key": "account_revenue_default",  "label": "Default Revenue Account (ID)",  "value_type": "integer", "default": None, "order": 8},
        {"key": "account_purchase_default", "label": "Default Purchase Account (ID)", "value_type": "integer", "default": None, "order": 9},
        {"key": "account_cogs_default",     "label": "Default COGS Account (ID)",     "value_type": "integer", "default": None, "order": 9},
        {"key": "accounting_mode_hpp",      "label": "Use COGS (HPP) Accounting Mode","value_type": "boolean", "default": False, "order": 9},
        {"key": "pos_invoice_prefix",   "label": "POS Invoice Prefix",       "value_type": "string",  "default": "POS",   "order": 10},
        {"key": "pos_allow_discount",   "label": "POS Allow Discount",       "value_type": "boolean", "default": True,    "order": 11},
        {"key": "pos_print_paper",      "label": "POS Receipt Paper Size",   "value_type": "string",  "default": "A5",    "order": 12},
        {"key": "pos_receipt_width_px", "label": "POS Receipt Width (px, for JPG)", "value_type": "integer", "default": 400, "order": 13},
        {"key": "pos_cash_journal",     "label": "POS Cash Journal Code",    "value_type": "string",  "default": "CASH",  "order": 14},
        {"key": "pos_enable_shift_journal", "label": "Post Shift Entries to Journal", "value_type": "boolean", "default": True, "order": 15},
        {"key": "pos_shift_report_footer",  "label": "Shift Report Footer Text",     "value_type": "text",    "default": "",  "order": 16},
    ],
)
