"""Standard / reference data seed — idempotent.

Covers all lookup tables that must exist before any transaction can be created:
CoA, UoMs, UoM groups, currencies, warehouses, payment modes, fiscal year,
doc series, tax charges, price types, customer groups, supplier groups,
CRM pipeline stages, product categories, and print/report templates.

Entry point: run_seed(company_id) → dict of created objects.
"""
from decimal import Decimal
from datetime import date
from arasCore.lib.core.extensions import db


# ── Currency ──────────────────────────────────────────────────────────────────
_CURRENCIES = [
    ("IDR", "Indonesian Rupiah", "Rp",   0),
    ("USD", "US Dollar",         "$",    2),
    ("EUR", "Euro",              "€",    2),
    ("SGD", "Singapore Dollar",  "S$",   2),
    ("MYR", "Malaysian Ringgit", "RM",   2),
]

def _seed_currencies():
    from app.erp.erp_config.models.currency import Currency
    out = {}
    for code, name, symbol, decimals in _CURRENCIES:
        c, _ = Currency.get_or_create(
            {"name": name, "symbol": symbol, "decimal_places": decimals,
             "is_active": True},
            code=code,
        )
        out[code] = c
    return out


# ── CoA ───────────────────────────────────────────────────────────────────────
def _seed_coa(company_id):
    from app.erp.erp_acc.seed_coa import seed_coa
    from app.erp.erp_config.models.company import Company
    slugs = seed_coa(company_id)
    company = Company.get(company_id)
    if company:
        mapping = {
            "acc_cash_default_id":       slugs.get("cash"),
            "acc_receivable_default_id": slugs.get("receivable"),
            "acc_payable_default_id":    slugs.get("payable"),
            "acc_income_default_id":     slugs.get("revenue"),
            "acc_inventory_default_id":  slugs.get("inventory"),
        }
        changed = False
        for field, acc in mapping.items():
            if acc and not getattr(company, field, None):
                setattr(company, field, acc.id)
                changed = True
        if changed:
            db.session.add(company)
            db.session.flush()
    return slugs


# ── UoM ───────────────────────────────────────────────────────────────────────
_UOMS = [
    "Pcs", "Box", "Carton", "Kilogram", "Gram", "Liter", "Milliliter",
    "Meter", "Centimeter", "Pack", "Dozen", "Pair", "Set", "Roll", "Sheet",
]

def _seed_uoms():
    from app.erp.erp_stock.models.uom import StockUom
    out = {}
    for name in _UOMS:
        u, _ = StockUom.get_or_create({}, name=name)
        out[name] = u
    return out


# ── Warehouses / Locations ────────────────────────────────────────────────────
_LOCATIONS = [
    # (name, location_type, parent_name)
    ("Main Warehouse",   "internal",  None),
    ("Store",            "internal",  None),
    ("Virtual",          "virtual",   None),
    ("Goods Received",   "transit",   "Main Warehouse"),
    ("Stock Shelf",      "internal",  "Main Warehouse"),
    ("Shipping Bay",     "transit",   "Main Warehouse"),
    ("POS Counter",      "internal",  "Store"),
]

def _seed_warehouses(company_id):
    from app.erp.erp_stock.models.warehouse import StockLocation
    created = {}
    for name, loc_type, parent_name in _LOCATIONS:
        parent = created.get(parent_name)
        obj, _ = StockLocation.get_or_create(
            {"location_type": loc_type,
             "parent_id": parent.id if parent else None,
             "company_id": company_id, "is_active": True},
            name=name, company_id=company_id,
        )
        created[name] = obj
    return created


# ── Payment Modes ─────────────────────────────────────────────────────────────
_MOPS = [
    ("Cash",         "cash"),
    ("QRIS",         "bank"),
    ("Bank Transfer","bank"),
    ("Credit Card",  "bank"),
    ("Debit Card",   "bank"),
]

def _seed_payment_modes(company_id, coa):
    from app.erp.erp_main.models.payment_mode import ModeOfPayment, CompanyPaymentAccount
    out = {}
    acc_map = {
        "Cash":          coa.get("cash"),
        "QRIS":          coa.get("cash"),
        "Bank Transfer": coa.get("cash"),
        "Credit Card":   coa.get("receivable"),
        "Debit Card":    coa.get("cash"),
    }
    for name, mop_type in _MOPS:
        mop, _ = ModeOfPayment.get_or_create(
            {"payment_type": mop_type, "is_active": True},
            name=name,
        )
        acc = acc_map.get(name)
        if acc:
            CompanyPaymentAccount.get_or_create(
                {"account_id": acc.id},
                company_id=company_id, mode_of_payment_id=mop.id,
            )
        out[name] = mop
    return out


# ── Fiscal Year + Periods ─────────────────────────────────────────────────────
def _seed_fiscal(company_id):
    from app.erp.erp_main.models.fiscal import FiscalYear, FiscalPeriod
    import calendar
    today = date.today()
    year = today.year
    fy, _ = FiscalYear.get_or_create(
        {"date_start": date(year, 1, 1), "date_end": date(year, 12, 31), "state": "open"},
        company_id=company_id, code=f"FY{year}",
    )
    for month in range(1, 13):
        last_day = calendar.monthrange(year, month)[1]
        FiscalPeriod.get_or_create(
            {"date_start": date(year, month, 1),
             "date_end":   date(year, month, last_day),
             "state": "open"},
            fiscal_year_id=fy.id,
            code=f"{year}-{month:02d}",
        )
    return fy


# ── Doc Series ────────────────────────────────────────────────────────────────
_DOC_SERIES = [
    ("accounting.sales_invoice",    "SINV",  "{prefix}/{YYYY}/{MM}/{seq}"),
    ("accounting.purchase_invoice", "PINV",  "{prefix}/{YYYY}/{MM}/{seq}"),
    ("accounting.journal_entry",    "JE",    "{prefix}/{YYYY}/{MM}/{seq}"),
    ("accounting.payment",          "PAY",   "{prefix}/{YYYY}/{MM}/{seq}"),
    ("stock.movement",              "STK",   "{prefix}/{YYYY}/{MM}/{seq}"),
    ("stock.delivery_order",        "DEL",   "{prefix}/{YYYY}/{MM}/{seq}"),
    ("stock.purchase_receipt",      "GRN",   "{prefix}/{YYYY}/{MM}/{seq}"),
    ("pos.shift",                   "SHIFT", "{prefix}/{YYYY}/{MM}/{seq}"),
    ("supplier.purchase_order",     "PO",    "{prefix}/{YYYY}/{MM}/{seq}"),
    ("sales.order",                 "SO",    "{prefix}/{YYYY}/{MM}/{seq}"),
]

def _seed_doc_series(company_id):
    from app.erp.erp_main.models.doc_series import DocSeries
    for code, prefix, fmt in _DOC_SERIES:
        DocSeries.get_or_create(
            {"prefix": prefix, "format": fmt, "padding": 5,
             "reset_period": "yearly", "next_value": 1, "is_active": True},
            company_id=company_id, code=code,
        )


# ── Tax Charges ───────────────────────────────────────────────────────────────
_CHARGES = [
    ("PPN11",  "PPN 11%",  "both",     "percent", Decimal("11.00"), False, 10),
    ("PPN0",   "PPN 0%",   "both",     "percent", Decimal("0.00"),  False, 20),
    ("WHT2",   "WHT 2%",   "purchase", "percent", Decimal("2.00"),  False, 30),
]

def _seed_charges(company_id):
    from app.erp.erp_config.models.tax import Charge
    for code, name, charge_type, calc_method, rate, is_inclusive, seq in _CHARGES:
        Charge.get_or_create(
            {"name": name, "charge_type": charge_type, "calc_method": calc_method,
             "rate": rate, "is_inclusive": is_inclusive, "sequence": seq},
            company_id=company_id, code=code,
        )


# ── Price Types ───────────────────────────────────────────────────────────────
_PRICE_TYPES = [
    ("Standard Selling",   "sales"),
    ("Standard Buying",    "purchase"),
    ("Wholesale Selling",  "sales"),
    ("Distributor Buying", "purchase"),
]

def _seed_price_types(company_id, currency_id):
    from app.erp.erp_config.models.price_type import StockPriceType
    out = {}
    for name, kind in _PRICE_TYPES:
        pt, _ = StockPriceType.get_or_create(
            {"currency_id": currency_id, "price_type": kind},
            company_id=company_id, name=name,
        )
        out[name] = pt
    return out


# ── Customer Groups ───────────────────────────────────────────────────────────
_CUSTOMER_GROUPS = [
    "Retail", "Wholesale", "Distributor", "Government", "VIP",
]

def _seed_customer_groups():
    from app.erp.erp_crm.models.customer_group import CrmCustomerGroup
    out = {}
    for name in _CUSTOMER_GROUPS:
        g, _ = CrmCustomerGroup.get_or_create({}, name=name)
        out[name] = g
    return out


# ── Supplier Groups ───────────────────────────────────────────────────────────
_SUPPLIER_GROUPS = [
    "Local", "Import", "Manufacturer", "Distributor", "Service Provider",
]

def _seed_supplier_groups():
    from app.erp.erp_sup.models.supplier_group import SupSupplierGroup
    out = {}
    for name in _SUPPLIER_GROUPS:
        g, _ = SupSupplierGroup.get_or_create({}, name=name)
        out[name] = g
    return out


# ── CRM Pipeline + Stages ─────────────────────────────────────────────────────
_PIPELINES = [
    ("Sales Pipeline", [
        ("New Lead",       "open",  10),
        ("Contacted",      "open",  20),
        ("Qualified",      "open",  30),
        ("Proposal Sent",  "open",  40),
        ("Negotiation",    "open",  50),
        ("Won",            "won",   60),
        ("Lost",           "lost",  70),
    ]),
]

def _seed_crm_pipelines(company_id):
    from app.erp.erp_crm.models.pipeline import CrmPipeline, CrmStage
    out = {}
    for pipeline_name, stages in _PIPELINES:
        pipeline, _ = CrmPipeline.get_or_create(
            {"company_id": company_id},
            name=pipeline_name, company_id=company_id,
        )
        out[pipeline_name] = {"pipeline": pipeline, "stages": {}}
        for stage_name, stage_type, seq in stages:
            stage, _ = CrmStage.get_or_create(
                {"stage_type": stage_type, "sequence": seq},
                pipeline_id=pipeline.id, name=stage_name,
            )
            out[pipeline_name]["stages"][stage_name] = stage
    return out


# ── Product Categories ────────────────────────────────────────────────────────
_CATEGORIES = [
    "Food & Beverage",
    "Electronics",
    "Apparel",
    "Raw Materials",
    "Packaging",
    "Consumables",
    "Services",
]

def _seed_product_categories(coa):
    from app.erp.erp_stock.models.product import StockProductCategory
    out = {}
    defaults = {
        "account_stock_id":    coa.get("inventory", None) and coa["inventory"].id,
        "account_cogs_id":     coa.get("cogs", None) and coa["cogs"].id,
        "account_revenue_id":  coa.get("revenue", None) and coa["revenue"].id,
        "account_purchase_id": coa.get("payable", None) and coa["payable"].id,
        "valuation_method":    "average",
    }
    for name in _CATEGORIES:
        cat, _ = StockProductCategory.get_or_create(
            {k: v for k, v in defaults.items() if v is not None},
            name=name,
        )
        out[name] = cat
    return out


# ── Print Templates ───────────────────────────────────────────────────────────
_PRINT_TEMPLATES = [
    {"doc_type": "sales.invoice",    "code": "default",
     "name": "Sales Invoice (Default)",
     "body_html": "<h1>Invoice {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
    {"doc_type": "purchase.invoice", "code": "default",
     "name": "Purchase Invoice (Default)",
     "body_html": "<h1>Bill {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
    {"doc_type": "pos.receipt",      "code": "default",
     "name": "POS Receipt (Default)",
     "body_html": "<h2>Receipt {{ doc.name }}</h2><p>Total: {{ doc.total }}</p>",
     "paper_size": "A5", "is_default": True},
    {"doc_type": "sales.order",      "code": "default",
     "name": "Sales Order (Default)",
     "body_html": "<h1>Sales Order {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
    {"doc_type": "purchase.order",   "code": "default",
     "name": "Purchase Order (Default)",
     "body_html": "<h1>Purchase Order {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
]

def _seed_print_templates(company_id):
    from app.erp.erp_main.models.print_template import PrintTemplate
    for t in _PRINT_TEMPLATES:
        PrintTemplate.get_or_create(
            {k: v for k, v in t.items() if k not in ("doc_type", "code")},
            company_id=company_id, doc_type=t["doc_type"], code=t["code"],
        )


# ── Reports ───────────────────────────────────────────────────────────────────
def _seed_reports():
    from app.erp.erp_main.report_seed import run_seed as seed_reports
    seed_reports()


# ── Public entry point ────────────────────────────────────────────────────────
def run_seed(company_id):
    """Seed all standard/reference data. Returns summary dict."""
    db.session.rollback()
    currencies     = _seed_currencies()
    idr            = currencies.get("IDR")
    coa            = _seed_coa(company_id)
    uoms           = _seed_uoms()
    warehouses     = _seed_warehouses(company_id)
    payment_modes  = _seed_payment_modes(company_id, coa)
    _seed_fiscal(company_id)
    _seed_doc_series(company_id)
    _seed_charges(company_id)
    price_types    = _seed_price_types(company_id, idr.id if idr else None)
    customer_groups = _seed_customer_groups()
    supplier_groups = _seed_supplier_groups()
    _seed_crm_pipelines(company_id)
    categories     = _seed_product_categories(coa)
    _seed_print_templates(company_id)
    _seed_reports()
    db.session.commit()
    return {
        "currencies": currencies,
        "coa": coa,
        "uoms": uoms,
        "warehouses": warehouses,
        "payment_modes": payment_modes,
        "price_types": price_types,
        "customer_groups": customer_groups,
        "supplier_groups": supplier_groups,
        "categories": categories,
    }
