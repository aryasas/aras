"""Seed data: UOM categories, UOMs, product categories (with COA links), and sample products."""
from arasCore.lib.core.extensions import db


UOM_CATEGORIES = ["Unit", "Berat", "Volume", "Panjang", "Waktu"]

UOMS = [
    # (name, code, category, uom_type, ratio)
    ("Pcs",     "pcs",  "Unit",   "reference", 1),
    ("Lusin",   "lsn",  "Unit",   "bigger",    12),
    ("Kodi",    "kdi",  "Unit",   "bigger",    20),
    ("Rim",     "rim",  "Unit",   "bigger",    500),
    ("Kg",      "kg",   "Berat",  "reference", 1),
    ("Gram",    "g",    "Berat",  "smaller",   0.001),
    ("Ton",     "ton",  "Berat",  "bigger",    1000),
    ("Liter",   "ltr",  "Volume", "reference", 1),
    ("ML",      "ml",   "Volume", "smaller",   0.001),
    ("Meter",   "m",    "Panjang","reference", 1),
    ("CM",      "cm",   "Panjang","smaller",   0.01),
    ("Jam",     "jam",  "Waktu",  "reference", 1),
    ("Menit",   "mnt",  "Waktu",  "smaller",   0.016667),
]

PRODUCT_CATEGORIES = [
    # (name, parent_name_or_None)
    ("Barang Dagangan", None),
    ("Makanan & Minuman", "Barang Dagangan"),
    ("Elektronik", "Barang Dagangan"),
    ("Alat Tulis Kantor", "Barang Dagangan"),
    ("Jasa", None),
]

# Produk sample — (code, name, category, uom_code, type, cost, price)
SAMPLE_PRODUCTS = [
    ("KS001", "Kopi Susu",          "Makanan & Minuman", "pcs", "consumable", 8000,   20000),
    ("CR001", "Croissant",          "Makanan & Minuman", "pcs", "consumable", 7000,   15000),
    ("JG001", "Jus Mangga",         "Makanan & Minuman", "pcs", "consumable", 6000,   18000),
    ("RT001", "Roti Bakar",         "Makanan & Minuman", "pcs", "consumable", 5000,   12000),
    ("NB001", "Notebook A5",        "Alat Tulis Kantor", "pcs", "storable",   8000,   15000),
    ("PN001", "Pulpen Ballpoint",   "Alat Tulis Kantor", "pcs", "storable",   2000,    5000),
    ("SP001", "Stapler Mini",       "Alat Tulis Kantor", "pcs", "storable",   15000,  35000),
    ("CB001", "Charger USB-C",      "Elektronik",        "pcs", "storable",   50000, 120000),
    ("HS001", "Headset Bluetooth",  "Elektronik",        "pcs", "storable",   80000, 200000),
    ("JAS001","Jasa Konsultasi",    "Jasa",              "jam", "service",    0,     150000),
]


def run_seed(app, company_id: int):
    with app.app_context():
        _seed_uom_categories()
        _seed_uoms()
        db.session.flush()
        _seed_product_categories(company_id)
        db.session.flush()
        _seed_products(company_id)
        db.session.commit()
        print("[seed] stock & product data seeded.")


def _seed_uom_categories():
    from aras.erp.erp_stock.models.uom import StockUomCategory
    for name in UOM_CATEGORIES:
        StockUomCategory.get_or_create({"is_active": True}, name=name)


def _seed_uoms():
    from aras.erp.erp_stock.models.uom import StockUom, StockUomCategory
    for name, code, cat_name, uom_type, ratio in UOMS:
        cat = StockUomCategory.find(name=cat_name)
        if not cat:
            continue
        StockUom.get_or_create(
            {"name": name, "category_id": cat.id, "uom_type": uom_type,
             "ratio": ratio, "rounding": 0.01, "is_active": True},
            code=code,
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
    from aras.erp.erp_core.models.currency import Currency

    for code, name, cat_name, uom_code, ptype, cost, price in SAMPLE_PRODUCTS:
        if StockProduct.exists(company_id=company_id, code=code):
            continue
        cat = StockProductCategory.find(name=cat_name)
        uom = StockUom.find(code=uom_code)
        if not uom:
            continue
        StockProduct.create({
            "company_id": company_id, "code": code, "name": name,
            "category_id": cat.id if cat else None,
            "uom_id": uom.id, "uom_sales_id": uom.id, "uom_purchase_id": uom.id,
            "is_stock_item": (ptype == "storable"), "use_price_table": False,
            "for_sales": True, "for_purchase": (ptype != "service"), "is_active": True,
        })
