# -*- coding: utf-8 -*-
from arasCore.lib.app_helper import AppHelper, MenuGroup, ResourceDef, SubHandler, CustomRoute

from aras.app_erp.erp_core.models import (
    CoreCompany, CoreCompanyBranch,
    CoreCurrency, CoreFxRate,
    CoreTax, CoreTaxGroup,
    CoreSetting, CoreSequence,
    CoreFiscalYear, CoreFiscalPeriod,
    CoreRole, CorePermission,
    CoreAttachment, CorePrintTemplate, CoreCustomField,
    ErpReport,
)
from aras.app_erp.erp_acc.models import (
    AccAccount, AccDefaultAccount,
    AccJournal, AccJournalEntry, AccJournalLine,
    AccAnalyticTag,
    AccBankStatement, AccBankStatementLine,
    AccSalesInvoice, AccSalesInvoiceLine,
    AccPurchaseInvoice, AccPurchaseInvoiceLine,
)
from aras.app_erp.erp_crm.models import (
    CrmCustomer, CrmContact,
    CrmLead, CrmPipeline, CrmStage, CrmActivity,
)
from aras.app_erp.erp_pos.models import (
    PosTerminal, PosSession,
    PosOrder, PosOrderLine, PosPayment,
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


class CompanyHandler(SubHandler):
    def list(self, query):
        return query.filter_by(is_active=True)


def _handle_post_journal():
    from flask import request, jsonify
    from arasCore.lib.extensions import db
    data = request.get_json() or {}
    entry_id = data.get("entry_id")
    if not entry_id:
        return jsonify({"ok": False, "error": "entry_id required"}), 400
    obj = AccJournalEntry.query.get_or_404(entry_id)
    if getattr(obj, "state", "draft") == "posted":
        return jsonify({"ok": False, "error": "Already posted"}), 400
    obj.state = "posted"
    db.session.commit()
    return jsonify({"ok": True, "data": {"id": obj.id, "state": obj.state}})


helper = AppHelper(
    name="erp",
    title="ERP",
    admin_icon="fa-building",
    admin_order=5,
    home_url="/erp/dashboard",
    menu_groups=[
        MenuGroup("Core", "fa-cogs", order=0, resources=[
            ResourceDef("company",        CoreCompany,       handler=CompanyHandler(), admin_list=True,
                        menu_title="Company", menu_icon="fa-building-o"),
            ResourceDef("company-branch", CoreCompanyBranch, admin_list=True,
                        menu_title="Branch", menu_icon="fa-code-fork"),
            ResourceDef("currency",       CoreCurrency,      admin_list=True,
                        menu_title="Currency", menu_icon="fa-dollar"),
            ResourceDef("fx-rate",        CoreFxRate,        admin_list=True,
                        menu_title="FX Rate", menu_icon="fa-exchange"),
            ResourceDef("tax",            CoreTax,           admin_list=True,
                        menu_title="Tax", menu_icon="fa-percent"),
            ResourceDef("tax-group",      CoreTaxGroup,      admin_list=True,
                        menu_title="Tax Group", menu_icon="fa-tags"),
            ResourceDef("fiscal-year",    CoreFiscalYear,    admin_list=True,
                        menu_title="Fiscal Year", menu_icon="fa-calendar"),
            ResourceDef("fiscal-period",  CoreFiscalPeriod,  admin_list=True,
                        menu_title="Fiscal Period", menu_icon="fa-calendar-o"),
            ResourceDef("sequence",       CoreSequence,      admin_list=True,
                        menu_title="Sequence", menu_icon="fa-sort-numeric-asc"),
            ResourceDef("setting",        CoreSetting,       admin_list=True,
                        menu_title="Settings", menu_icon="fa-sliders"),
            ResourceDef("custom-field",   CoreCustomField,   admin_list=True,
                        menu_title="Custom Fields", menu_icon="fa-list-alt"),
            ResourceDef("print-template", CorePrintTemplate, admin_list=True,
                        menu_title="Print Templates", menu_icon="fa-print"),
            ResourceDef("role",           CoreRole,          admin_list=True,
                        menu_title="Roles", menu_icon="fa-shield"),
            ResourceDef("permission",     CorePermission,    admin_list=True,
                        menu_title="Permissions", menu_icon="fa-key"),
            ResourceDef("attachment",     CoreAttachment,    admin_list=False),
        ]),

        MenuGroup("Accounting", "fa-calculator", order=1, resources=[
            ResourceDef("acc/account",      AccAccount,             admin_list=True,
                        menu_title="Chart of Accounts", menu_icon="fa-sitemap"),
            ResourceDef("acc/journal",      AccJournal,             admin_list=True,
                        menu_title="Journals", menu_icon="fa-book"),
            ResourceDef("acc/entry",        AccJournalEntry,        handler=JournalEntryHandler(), admin_list=True,
                        menu_title="Journal Entries", menu_icon="fa-pencil-square-o"),
            ResourceDef("acc/line",         AccJournalLine,         admin_list=False),
            ResourceDef("acc/default",      AccDefaultAccount,      admin_list=True,
                        menu_title="Default Accounts", menu_icon="fa-link"),
            ResourceDef("acc/analytic-tag", AccAnalyticTag,         admin_list=True,
                        menu_title="Analytic Tags", menu_icon="fa-tag"),
            ResourceDef("acc/bank",         AccBankStatement,       admin_list=True,
                        menu_title="Bank Statements", menu_icon="fa-bank"),
            ResourceDef("acc/bank-line",    AccBankStatementLine,   admin_list=False),
            ResourceDef("acc/sales-invoice",       AccSalesInvoice,       admin_list=True,
                        menu_title="Sales Invoices", menu_icon="fa-file-text-o"),
            ResourceDef("acc/sales-invoice-line",  AccSalesInvoiceLine,   admin_list=False),
            ResourceDef("acc/purchase-invoice",    AccPurchaseInvoice,    admin_list=True,
                        menu_title="Purchase Invoices", menu_icon="fa-file-o"),
            ResourceDef("acc/purchase-invoice-line", AccPurchaseInvoiceLine, admin_list=False),
        ]),

        MenuGroup("CRM", "fa-handshake-o", order=2, resources=[
            ResourceDef("crm/customer",  CrmCustomer,  admin_list=True,
                        menu_title="Customers", menu_icon="fa-user-circle"),
            ResourceDef("crm/contact",   CrmContact,   admin_list=True,
                        menu_title="Contacts", menu_icon="fa-address-book"),
            ResourceDef("crm/lead",      CrmLead,      admin_list=True,
                        menu_title="Leads", menu_icon="fa-filter"),
            ResourceDef("crm/pipeline",  CrmPipeline,  admin_list=True,
                        menu_title="Pipelines", menu_icon="fa-random"),
            ResourceDef("crm/stage",     CrmStage,     admin_list=True,
                        menu_title="Stages", menu_icon="fa-flag"),
            ResourceDef("crm/activity",  CrmActivity,  admin_list=False),
        ]),

        MenuGroup("Point of Sale", "fa-shopping-cart", order=3, resources=[
            ResourceDef("pos/terminal",   PosTerminal,  admin_list=True,
                        menu_title="Terminals", menu_icon="fa-desktop"),
            ResourceDef("pos/session",    PosSession,   admin_list=True,
                        menu_title="Sessions", menu_icon="fa-clock-o"),
            ResourceDef("pos/order",      PosOrder,     admin_list=True,
                        menu_title="Orders", menu_icon="fa-list"),
            ResourceDef("pos/order-line", PosOrderLine, admin_list=False),
            ResourceDef("pos/payment",    PosPayment,   admin_list=False),
        ]),

        MenuGroup("Reports", "fa-bar-chart", order=4, resources=[
            ResourceDef("report", ErpReport, admin_list=True,
                        menu_title="Reports", menu_icon="fa-bar-chart"),
        ]),

        MenuGroup("Stock", "fa-cubes", order=5, resources=[
            ResourceDef("stock/uom-category",     StockUomCategory,     admin_list=True,
                        menu_title="UOM Categories", menu_icon="fa-th-large"),
            ResourceDef("stock/uom",              StockUom,             admin_list=True,
                        menu_title="Units of Measure", menu_icon="fa-balance-scale"),
            ResourceDef("stock/uom-conversion",   StockUomConversion,   admin_list=True,
                        menu_title="UOM Conversions", menu_icon="fa-exchange"),
            ResourceDef("stock/product-category", StockProductCategory, admin_list=True,
                        menu_title="Product Categories", menu_icon="fa-folder-o"),
            ResourceDef("stock/product",          StockProduct,         admin_list=True,
                        menu_title="Products", menu_icon="fa-cube"),
            ResourceDef("stock/product-uom",      StockProductUom,      admin_list=False),
            ResourceDef("stock/product-price",    StockProductPrice,    admin_list=True,
                        menu_title="Product Prices", menu_icon="fa-money"),
            ResourceDef("stock/product-bundle",   StockProductBundle,   admin_list=True,
                        menu_title="Product Bundles", menu_icon="fa-cubes"),
            ResourceDef("stock/product-account",  StockProductAccountLink, admin_list=True,
                        menu_title="Product Accounts", menu_icon="fa-link"),
            ResourceDef("stock/pricelist",        StockPriceList,       admin_list=True,
                        menu_title="Price Lists", menu_icon="fa-tag"),
            ResourceDef("stock/pricelist-item",   StockPriceListItem,   admin_list=False),
            ResourceDef("stock/warehouse",        StockWarehouse,       admin_list=True,
                        menu_title="Warehouses", menu_icon="fa-building-o"),
            ResourceDef("stock/location",         StockLocation,        admin_list=True,
                        menu_title="Locations", menu_icon="fa-map-marker"),
            ResourceDef("stock/movement",         StockMovement,        admin_list=True,
                        menu_title="Stock Movements", menu_icon="fa-exchange"),
            ResourceDef("stock/movement-line",    StockMovementLine,    admin_list=False),
            ResourceDef("stock/valuation",        StockValuation,       admin_list=True,
                        menu_title="Stock Valuation", menu_icon="fa-bar-chart"),
        ]),
    ],
    custom_routes=[
        CustomRoute("/acc/entry/post", _handle_post_journal, methods=["POST"], require_auth=True),
    ],
)
