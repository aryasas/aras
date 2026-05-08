"""Comprehensive ERP seed.

Idempotent — safe to run multiple times (uses get_or_create everywhere).
Covers: COA, DocSeries defaults, PPN 11%, default Print/Report templates,
UoM (with conversions), Product Categories, Products + price tables
(Standard Buying/Standard Selling), Product Bundle.

Entry point: run_seed(company)
"""
from decimal import Decimal
from arasCore.lib.core.extensions import db


# ── DocSeries defaults ────────────────────────────────────────────────────────
_DOC_SERIES = [
    # (code, prefix, format)
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


# ── PPN 11% charge ────────────────────────────────────────────────────────────
def _seed_charges(company_id):
    from app.erp.erp_config.models.tax import Charge
    Charge.get_or_create(
        {"name": "PPN 11%", "charge_type": "both", "calc_method": "percent",
         "rate": Decimal("11.00"), "is_inclusive": False, "sequence": 10},
        company_id=company_id, code="PPN11",
    )




# ── Price Types (named price groups) ──────────────────────────────────────────
_PRICE_TYPES = [
    ("Standard Selling", "sales"),
    ("Standard Buying",  "purchase"),
]


def _seed_price_types(company_id, currency_id):
    from app.erp.erp_config.models.price_type import StockPriceType
    out = {}
    for name, kind in _PRICE_TYPES:
        pt, created = StockPriceType.get_or_create(
            {"currency_id": currency_id, "price_type": kind},
            company_id=company_id, name=name,
        )
        # Backfill kind on rows seeded before the column existed
        if not created and getattr(pt, "price_type", None) != kind:
            pt.price_type = kind
        out[kind] = pt
    return out


def _backfill_price_type_links(price_types):
    """No longer needed — kept as stub for backward compat."""
    return None


# ── UoM with conversions ──────────────────────────────────────────────────────
_UOMS = [
    ("PCS", "Pcs"),
    ("BOX", "Box"),
    ("CTN", "Carton"),
    ("KG",  "Kilogram"),
    ("G",   "Gram"),
    ("L",   "Liter"),
    ("ML",  "Milliliter"),
]


def _seed_uoms():
    from app.erp.erp_stock.models.uom import StockUom
    out = {}
    for code, name in _UOMS:
        u, _ = StockUom.get_or_create({}, name=name)
        out[code] = u
    return out


# ── Products + price tables + bundle ──────────────────────────────────────────
def _seed_products(company_id, coa, uoms, price_types):
    from app.erp.erp_stock.models.product import (
        StockProductCategory, StockProduct, StockProductUom,
        StockPriceList, StockProductBundle,
    )
    from app.erp.erp_config.models.currency import Currency

    # Category
    cat, _ = StockProductCategory.get_or_create(
        {
            "account_stock_id":    coa["inventory"].id,
            "account_cogs_id":     coa["cogs"].id,
            "account_revenue_id":  coa["revenue"].id,
            "account_purchase_id": coa["payable"].id,
            "valuation_method":    "average",
        },
        name="Makanan & Minuman",
    )

    currency = Currency.find(code="IDR") or Currency.query.first()
    pcs = uoms["PCS"]
    box = uoms["BOX"]
    ctn = uoms["CTN"]

    # Stockable product with UoM conversions: Box=12 Pcs, Carton=144 Pcs
    coffee, _ = StockProduct.get_or_create(
        {
            "name": "Kopi Susu Test", "company_id": company_id,
            "category_id": cat.id, "uom_id": pcs.id,
            "for_sales": True, "for_purchase": True, "is_stock_item": True,
        },
        code="KST", company_id=company_id,
    )
    # UoM conversions
    StockProductUom.get_or_create(
        {"factor": Decimal("12"), "is_active": True},
        product_id=coffee.id, uom_id=box.id,
    )
    StockProductUom.get_or_create(
        {"factor": Decimal("144"), "is_active": True},
        product_id=coffee.id, uom_id=ctn.id,
    )
    # Standard Buying / Standard Selling per unit
    for ptype, price in [("sales", Decimal("25000")), ("purchase", Decimal("10000"))]:
        StockPriceList.get_or_create(
            {"price": price, "min_qty": 1, "uom_id": pcs.id,
             "is_active": True, "currency_id": currency.id},
            product_id=coffee.id, price_type_id=price_types[ptype].id, uom_id=pcs.id,
        )

    # Companion product — for bundle
    snack, _ = StockProduct.get_or_create(
        {
            "name": "Snack Pendamping", "company_id": company_id,
            "category_id": cat.id, "uom_id": pcs.id,
            "for_sales": True, "for_purchase": True, "is_stock_item": True,
        },
        code="SNK", company_id=company_id,
    )
    for ptype, price in [("sales", Decimal("8000")), ("purchase", Decimal("3000"))]:
        StockPriceList.get_or_create(
            {"price": price, "min_qty": 1, "uom_id": pcs.id,
             "is_active": True, "currency_id": currency.id},
            product_id=snack.id, price_type_id=price_types[ptype].id, uom_id=pcs.id,
        )

    # Bundle product (non-stock kit) — 1 Coffee + 1 Snack
    combo, _ = StockProduct.get_or_create(
        {
            "name": "Combo Kopi+Snack", "company_id": company_id,
            "category_id": cat.id, "uom_id": pcs.id,
            "for_sales": True, "for_purchase": False, "is_stock_item": False,
        },
        code="CMB", company_id=company_id,
    )
    StockProductBundle.get_or_create(
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=combo.id, component_id=coffee.id,
    )
    StockProductBundle.get_or_create(
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=combo.id, component_id=snack.id,
    )
    StockPriceList.get_or_create(
        {"price": Decimal("30000"), "min_qty": 1, "uom_id": pcs.id,
         "is_active": True, "currency_id": currency.id},
        product_id=combo.id, price_type_id=price_types["sales"].id, uom_id=pcs.id,
    )
    return {"category": cat, "coffee": coffee, "snack": snack, "combo": combo}


# ── Print/Report templates ────────────────────────────────────────────────────
_PRINT_TEMPLATES = [
    {"doc_type": "sales.invoice",    "code": "default", "name": "Sales Invoice (Default)",
     "body_html": "<h1>Invoice {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
    {"doc_type": "purchase.invoice", "code": "default", "name": "Purchase Invoice (Default)",
     "body_html": "<h1>Bill {{ doc.name }}</h1><p>Total: {{ doc.total }}</p>",
     "is_default": True},
    {"doc_type": "pos.receipt",      "code": "default", "name": "POS Receipt (Default)",
     "body_html": "<h2>Receipt {{ doc.name }}</h2><p>Total: {{ doc.total }}</p>",
     "paper_size": "A5", "is_default": True},
]


def _seed_print_templates(company_id):
    from app.erp.erp_main.models.print_template import PrintTemplate
    for t in _PRINT_TEMPLATES:
        PrintTemplate.get_or_create(
            {**{k: v for k, v in t.items() if k not in ("doc_type", "code")}},
            company_id=company_id, doc_type=t["doc_type"], code=t["code"],
        )


_REPORTS = [
    {"name": "trial_balance", "title": "Trial Balance", "module": "accounting",
     "report_type": "query", "render_mode": "list"},
    {"name": "general_ledger", "title": "General Ledger", "module": "accounting",
     "report_type": "query", "render_mode": "list"},
    {"name": "stock_summary", "title": "Stock Summary", "module": "stock",
     "report_type": "query", "render_mode": "list"},
    {"name": "sales_by_product", "title": "Sales by Product", "module": "sales",
     "report_type": "query", "render_mode": "list"},
]


def _seed_reports(company_id):
    from app.erp.erp_main.models.report import ErpReport
    for r in _REPORTS:
        ErpReport.get_or_create(
            {**{k: v for k, v in r.items() if k != "name"}, "company_id": company_id},
            name=r["name"],
        )


# ── Public entry point ────────────────────────────────────────────────────────
def run_seed(company_id, coa):
    """Run all seed steps. Returns dict of created/found objects."""
    from app.erp.erp_config.models.currency import Currency
    cur = Currency.find(code="IDR") or Currency.query.first()
    _seed_doc_series(company_id)
    _seed_charges(company_id)
    price_types = _seed_price_types(company_id, cur.id)
    _backfill_price_type_links(price_types)
    uoms = _seed_uoms()
    products = _seed_products(company_id, coa, uoms, price_types)
    _seed_print_templates(company_id)
    _seed_reports(company_id)
    db.session.commit()
    return {"uoms": uoms, "price_types": price_types, **products}
