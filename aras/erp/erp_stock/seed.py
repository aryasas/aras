"""Seed data: UOM categories, UOMs, product categories (with COA links), and sample products."""
from arasCore.lib.core.extensions import db


UOMS = [
    "Pcs",
    "Lusin",
    "Kodi",
    "Rim",
    "Kg",
    "Gram",
    "Ton",
    "Liter",
    "ML",
    "Meter",
    "CM",
    "Jam",
    "Menit",
]

PRODUCT_CATEGORIES = [
    # (name, parent_name_or_None)
    ("Barang Dagangan", None),
    ("Makanan & Minuman", "Barang Dagangan"),
    ("Elektronik", "Barang Dagangan"),
    ("Alat Tulis Kantor", "Barang Dagangan"),
    ("Jasa", None),
]

# Produk sample — (code, name, category, uom_name, type, cost, price)
SAMPLE_PRODUCTS = [
    ("KS001", "Kopi Susu",          "Makanan & Minuman", "Pcs", "consumable", 8000,   20000),
    ("CR001", "Croissant",          "Makanan & Minuman", "Pcs", "consumable", 7000,   15000),
    ("JG001", "Jus Mangga",         "Makanan & Minuman", "Pcs", "consumable", 6000,   18000),
    ("RT001", "Roti Bakar",         "Makanan & Minuman", "Pcs", "consumable", 5000,   12000),
    ("NB001", "Notebook A5",        "Alat Tulis Kantor", "Pcs", "storable",   8000,   15000),
    ("PN001", "Pulpen Ballpoint",   "Alat Tulis Kantor", "Pcs", "storable",   2000,    5000),
    ("SP001", "Stapler Mini",       "Alat Tulis Kantor", "Pcs", "storable",   15000,  35000),
    ("CB001", "Charger USB-C",      "Elektronik",        "Pcs", "storable",   50000, 120000),
    ("HS001", "Headset Bluetooth",  "Elektronik",        "Pcs", "storable",   80000, 200000),
    ("JAS001","Jasa Konsultasi",    "Jasa",              "Jam", "service",    0,     150000),
]


def run_seed(app, company_id: int):
    with app.app_context():
        _seed_uoms()
        db.session.flush()
        _seed_product_categories(company_id)
        db.session.flush()
        _seed_products(company_id)
        db.session.commit()
        print("[seed] stock & product data seeded.")


def _seed_uoms():
    from aras.erp.erp_stock.models.uom import StockUom
    for name in UOMS:
        StockUom.get_or_create(
            {},
            name=name,
        )


def _seed_product_categories(company_id: int):
    from aras.erp.erp_stock.models.product import StockProductCategory
    from aras.erp.erp_acc.services.posting import get_default_account

    try:
        income_acc_id = get_default_account(company_id, "income_default")
        cogs_acc_id   = get_default_account(company_id, "cogs_default")
        stock_acc_id  = get_default_account(company_id, "inventory_default")
    except ValueError:
        income_acc_id = cogs_acc_id = stock_acc_id = None

    parent_map = {}
    for name, parent_name in PRODUCT_CATEGORIES:
        parent = parent_map.get(parent_name) if parent_name else None
        cat, _ = StockProductCategory.get_or_create(
            {"parent_id": parent.id if parent else None,
             "account_revenue_id": income_acc_id, "account_cogs_id": cogs_acc_id,
             "account_stock_id": stock_acc_id, "valuation_method": "average", "is_active": True},
            name=name,
        )
        parent_map[name] = cat


def _seed_products(company_id: int):
    from aras.erp.erp_stock.models.product import StockProduct, StockProductCategory
    from aras.erp.erp_stock.models.uom import StockUom

    for code, name, cat_name, uom_name, ptype, cost, price in SAMPLE_PRODUCTS:
        if StockProduct.exists(company_id=company_id, code=code):
            continue
        cat = StockProductCategory.find(name=cat_name)
        uom = StockUom.find(name=uom_name)
        if not uom:
            continue
        StockProduct.create({
            "company_id": company_id, "code": code, "name": name,
            "category_id": cat.id if cat else None,
            "uom_id": uom.id, "uom_sales_id": uom.id, "uom_purchase_id": uom.id,
            "for_sales": True, "for_purchase": (ptype != "service"), "is_active": True,
        })
