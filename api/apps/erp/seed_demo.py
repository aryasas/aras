"""Demo data seed — idempotent.

Requires standard seed to have run first (CoA, UoMs, warehouses, payment modes,
customer/supplier groups, price types, fiscal year, doc series).

Covers: customers, suppliers, products (stockable + service + bundle),
UoM conversions, price lists, opening stock movements.

Entry point: run_seed(company_id) → dict of created objects.
"""
from decimal import Decimal
from datetime import date
from sqlalchemy.orm import Session
from core import Aras # Import Aras to access registry

# ERP Models (accessed via Aras.Model._registry)


# ── helpers ───────────────────────────────────────────────────────────────────
def _uom(db: Session, name: str):
    Uom = Aras.Model._registry["Uom"]
    return Uom.find(db, name=name)


def _category(db: Session, name: str):
    ProductCategory = Aras.Model._registry["ProductCategory"]
    return ProductCategory.find(db, name=name)


def _price_type(db: Session, company_id: int, name: str):
    PriceType = Aras.Model._registry["PriceType"]
    return PriceType.find(db, name=name)


def _location(db: Session, company_id: int, name: str):
    Location = Aras.Model._registry["Location"]
    return Location.find(db, company_id=company_id, name=name)


def _currency(db: Session, code: str):
    Currency = Aras.Model._registry["Currency"]
    return Currency.find(db, code=code)


# ── Customers ─────────────────────────────────────────────────────────────────
_CUSTOMERS = [
    # (code, name, group_name, phone, email)
    ("C001", "Toko Maju Bersama",   "Retail",      "0812-0001-0001", "toko.maju@example.com"),
    ("C002", "CV Sejahtera Abadi",  "Wholesale",   "0812-0002-0002", "sejahtera@example.com"),
    ("C003", "PT Distribusi Nusa",  "Distributor", "0812-0003-0003", "distribusi@example.com"),
    ("C004", "Warung Pak Budi",     "Retail",      "0812-0004-0004", None),
    ("C005", "Koperasi Karyawan",   "Government",  "0812-0005-0005", "koperasi@example.com"),
]

def _seed_customers(db: Session, company_id: int):
    Customer = Aras.Model._registry["Customer"] # Get Customer model from registry
    idr = _currency(db, "IDR")
    out = {}
    for code, name, group_name, phone, email in _CUSTOMERS: # group_name is unused but kept for iteration
        obj, _ = Customer.get_or_create(
            db,
            {
                "name": name,
                "currency_id": idr.id if idr else None,
                "phone": phone,
                "email": email,
            },
            company_id=company_id, code=code,
        )
        out[code] = obj
    return out


# ── Suppliers ─────────────────────────────────────────────────────────────────
_SUPPLIERS = [
    # (code, name, group_name, phone, email)
    ("S001", "PT Sumber Makmur",     "Manufacturer", "0811-0001-0001", "sumber@example.com"),
    ("S002", "CV Bahan Prima",       "Local",        "0811-0002-0002", "prima@example.com"),
    ("S003", "Importir Asia Jaya",   "Import",       "0811-0003-0003", "asiajaya@example.com"),
    ("S004", "Jasa Ekspedisi Cepat", "Service Provider", "0811-0004-0004", None),
]

def _seed_suppliers(db: Session, company_id: int):
    Supplier = Aras.Model._registry["Supplier"] # Get Supplier model from registry
    idr = _currency(db, "IDR")
    out = {}
    for code, name, group_name, phone, email in _SUPPLIERS: # group_name is unused but kept for iteration
        obj, _ = Supplier.get_or_create(
            db,
            {
                "name": name,
                "currency_id": idr.id if idr else None,
                "phone": phone,
                "email": email,
            },
            company_id=company_id, code=code,
        )
        out[code] = obj
    return out


# ── Products ──────────────────────────────────────────────────────────────────
def _seed_products(db: Session, company_id: int):
    Product = Aras.Model._registry["Product"]
    ProductUom = Aras.Model._registry["ProductUom"]
    PriceList = Aras.Model._registry["PriceList"]
    PromoBundle = Aras.Model._registry["PromoBundle"]
    PromoBundleItem = Aras.Model._registry["PromoBundleItem"]

    # Ensure required UoMs exist
    Uom = Aras.Model._registry["Uom"]
    for uom_name, uom_code in [("Carton", "CTN"), ("Gram", "G"), ("Milliliter", "ML")]:
        Uom.get_or_create(db, {"code": uom_code}, name=uom_name)
    db.flush()

    idr = _currency(db, "IDR")
    pcs = _uom(db, "Pieces")   # "Pieces" is seeded by core setup
    box = _uom(db, "Box")
    ctn = _uom(db, "Carton")
    kg  = _uom(db, "Kilogram")
    g   = _uom(db, "Gram")
    ltr = _uom(db, "Liter")
    ml  = _uom(db, "Milliliter")

    cat_fnb   = _category(db, "Food & Beverage")
    cat_elec  = _category(db, "Electronics")
    cat_svc   = _category(db, "Services")
    cat_raw   = _category(db, "Raw Materials")

    pt_sell = _price_type(db, company_id, "Standard Selling")
    pt_buy  = _price_type(db, company_id, "Standard Buying")

    out = {}

    def _make(code, name, cat, uom, for_sales, for_purchase, is_stock, sell_price, buy_price, sell_uom=None):
        prod, _ = Product.get_or_create(
            db,
            {
                "name": name, "company_id": company_id,
                "category_id": cat.id if cat else None,
                "uom_id": uom.id,
                "for_sales": for_sales, "for_purchase": for_purchase,
                "is_stock_item": is_stock, "is_active": True,
            },
            code=code, company_id=company_id,
        )
        suom = sell_uom or uom
        if pt_sell and sell_price is not None:
            PriceList.get_or_create(
                db,
                {"price": Decimal(str(sell_price)), "min_qty": 1,
                 "uom_id": suom.id, "is_active": True,
                 "currency_id": idr.id if idr else None},
                product_id=prod.id, price_type_id=pt_sell.id, uom_id=suom.id,
            )
        if pt_buy and buy_price is not None:
            PriceList.get_or_create(
                db,
                {"price": Decimal(str(buy_price)), "min_qty": 1,
                 "uom_id": uom.id, "is_active": True,
                 "currency_id": idr.id if idr else None},
                product_id=prod.id, price_type_id=pt_buy.id, uom_id=uom.id,
            )
        return prod

    # Food & Beverage — stockable
    coffee = _make("P-KOPI-001", "Kopi Arabica Premium",   cat_fnb,  pcs,  True,  True,  True,  28000,  11000)
    tea    = _make("P-TEH-001",  "Teh Hijau Organik",      cat_fnb,  pcs,  True,  True,  True,  18000,   7000)
    sugar  = _make("P-GUL-001",  "Gula Pasir 1 Kg",        cat_fnb,  kg,   True,  True,  True,  15000,  12000)
    water  = _make("P-AIR-001",  "Air Mineral 600 ml",     cat_fnb,  pcs,  True,  True,  True,   5000,   2500)
    syrup  = _make("P-SIR-001",  "Sirup Cocopandan 650 ml",cat_fnb,  pcs,  True,  True,  True,  35000,  22000)
    snack  = _make("P-SNK-001",  "Keripik Singkong",       cat_fnb,  pcs,  True,  True,  True,  12000,   5000)

    # Electronics — stockable
    cable  = _make("P-CBL-001",  "Kabel USB Type-C 1m",   cat_elec, pcs,  True,  True,  True,  45000,  20000)
    charger= _make("P-CHR-001",  "Adaptor 65W GaN",        cat_elec, pcs,  True,  True,  True, 195000,  90000)

    # Raw material
    flour  = _make("P-TRG-001",  "Tepung Terigu 25 Kg",   cat_raw,  kg,   False, True,  True,  None,    9500)

    # Service — non-stock
    deliv  = _make("P-SVC-DEL",  "Biaya Pengiriman",      cat_svc,  pcs,  True,  False, False, 25000,   None)
    instal = _make("P-SVC-INS",  "Biaya Instalasi",       cat_svc,  pcs,  True,  False, False, 150000,  None)

    out.update({
        "coffee": coffee, "tea": tea, "sugar": sugar, "water": water,
        "syrup": syrup, "snack": snack, "cable": cable, "charger": charger,
        "flour": flour, "delivery": deliv, "install": instal,
    })

    # ── UoM conversions ──────────────────────────────────────────────────────
    # Coffee: Box = 12 Pcs, Carton = 144 Pcs
    if box:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("12")},
            product_id=coffee.id, uom_id=box.id,
        )
    if ctn:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("144")},
            product_id=coffee.id, uom_id=ctn.id,
        )
    # Tea: Box = 24 Pcs
    if box:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("24")},
            product_id=tea.id, uom_id=box.id,
        )
    # Sugar: Gram = 0.001 Kg
    if g:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("0.001")},
            product_id=sugar.id, uom_id=g.id,
        )
    # Syrup: 650 ml per bottle (base Liter → Milliliter)
    if ml and ltr:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("0.001")},
            product_id=syrup.id, uom_id=ml.id,
        )
    # Water: Box = 24 Pcs
    if box:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("24")},
            product_id=water.id, uom_id=box.id,
        )
    # Snack: Box = 20 Pcs, Carton = 200 Pcs
    if box:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("20")},
            product_id=snack.id, uom_id=box.id,
        )
    if ctn:
        ProductUom.get_or_create(
            db,
            {"factor": Decimal("200")},
            product_id=snack.id, uom_id=ctn.id,
        )

    # ── Price breaks (wholesale — box pricing) ────────────────────────────────
    if pt_sell and box and idr:
        PriceList.get_or_create(
            db,
            {"price": Decimal("300000"), "min_qty": 1, "uom_id": box.id,
             "is_active": True, "currency_id": idr.id},
            product_id=coffee.id, price_type_id=pt_sell.id, uom_id=box.id,
        )

    # ── Bundle: Coffee Starter Pack = 1 Coffee + 1 Tea + 1 Sugar ─────────────
    # Create the Product for the bundle (sellable item)
    bundle_product = _make("P-BSP-001", "Coffee Starter Pack", cat_fnb, pcs, True, False, False, 55000, None)
    out["bundle_starter"] = bundle_product

    # Create the PromoBundle header for the bundle definition
    promo_bundle, _ = PromoBundle.get_or_create(
        db,
        {"name": "Coffee Starter Pack", "company_id": company_id},
        code="P-BSP-001", company_id=company_id,
    )

    # Create PromoBundleItems for the components
    PromoBundleItem.get_or_create(
        db,
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=promo_bundle.id, product_id=coffee.id,
    )
    PromoBundleItem.get_or_create(
        db,
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=promo_bundle.id, product_id=tea.id,
    )
    PromoBundleItem.get_or_create(
        db,
        {"qty": Decimal("1"), "uom_id": kg.id},
        bundle_id=promo_bundle.id, product_id=sugar.id,
    )

    return out


# ── Opening Stock ─────────────────────────────────────────────────────────────
def _seed_opening_stock(db: Session, company_id: int, products):
    """Create a single opening-stock movement (status=Draft, not posted).
    This gives the demo something to look at without triggering valuation logic.
    """
    StockMovement = Aras.Model._registry["StockMovement"]
    StockMovementLine = Aras.Model._registry["StockMovementLine"]
    Location = Aras.Model._registry["Location"]

    wh_loc, _ = Location.get_or_create(
        db,
        {"name": "Main Warehouse", "is_group": True, "location_type": "Internal"},
        company_id=company_id, code="WH"
    )
    
    loc, _ = Location.get_or_create(
        db,
        {"name": "Stock Shelf", "parent_id": wh_loc.id, "location_type": "Internal"},
        company_id=company_id, code="SHELF-1"
    )

    pcs = _uom(db, "Pieces")
    kg  = _uom(db, "Kilogram")

    # Only seed if no opening movement exists yet
    existing = StockMovement.find(db, company_id=company_id, move_type="Opening")
    if existing:
        return existing

    idr = _currency(db, "IDR")
    mv = StockMovement.create(db, {
        "company_id":      company_id,
        "number":          "OPEN/DEMO/001",
        "move_type":       "Opening",
        "currency_id":     idr.id if idr else None,
        "status":          "Draft",
        "doc_date":        date.today(),
        "to_location_id":  wh_loc.id,
        "notes":           "Demo opening stock",
    })

    # lines: (product, qty, uom, unit_cost)
    lines = [
        (products.get("coffee"),  100, pcs,  11000),
        (products.get("tea"),     200, pcs,   7000),
        (products.get("sugar"),    50, kg,   12000),
        (products.get("water"),   300, pcs,   2500),
        (products.get("syrup"),    48, pcs,  22000),
        (products.get("snack"),   150, pcs,   5000),
        (products.get("cable"),    30, pcs,  20000),
        (products.get("charger"), 20,  pcs,  90000),
    ]
    for prod, qty, uom, cost in lines:
        if not prod or not uom:
            continue
        StockMovementLine.create(db, {
            "movement_id":    mv.id,
            "product_id":     prod.id,
            "qty":            float(qty),
            "uom_id":         uom.id,
            "unit_cost":      float(cost),
            "to_location_id": loc.id,
        })
    return mv


# ── POS Terminal ──────────────────────────────────────────────────────────────
def _seed_pos_terminal(db: Session, company_id: int):
    PosTerminal = Aras.Model._registry["PosTerminal"]
    ModeOfPayment = Aras.Model._registry["ModeOfPayment"]
    Location = Aras.Model._registry["Location"]

    loc = Location.find(db, company_id=company_id, code="SHELF-1")
    cash_mop = ModeOfPayment.find(db, name="Cash")

    terminal, _ = PosTerminal.get_or_create(
        db,
        {
            "location_id": loc.id if loc else None,
            "default_mop_id": cash_mop.id if cash_mop else None,
        },
        name="Kasir Utama",
    )
    return terminal


# ── CRM Demo Leads ────────────────────────────────────────────────────────────
def _seed_demo_leads(db: Session, company_id: int, customers):
    Pipeline = Aras.Model._registry["Pipeline"]
    Stage = Aras.Model._registry["Stage"]
    Lead = Aras.Model._registry["Lead"]

    pipeline = Pipeline.find(db, name="Sales Pipeline")
    if not pipeline:
        return []

    stage_new  = Stage.find(db, pipeline_id=pipeline.id, name="New Lead")
    stage_qual = Stage.find(db, pipeline_id=pipeline.id, name="Qualified")
    stage_prop = Stage.find(db, pipeline_id=pipeline.id, name="Proposal Sent")

    leads_data = [
        ("Penawaran Kopi Arabica",     customers.get("C001"), stage_new),
        ("Proposal Grosir Minuman",    customers.get("C002"), stage_qual),
        ("Follow-up Distributor Nusa", customers.get("C003"), stage_prop),
    ]
    leads = []
    for name, customer, stage in leads_data:
        lead, _ = Lead.get_or_create(
            db,
            {
                "customer_id": customer.id if customer else None,
                "stage_id":    stage.id if stage else None,
                "company_id":  company_id,
            },
            name=name, company_id=company_id,
        )
        leads.append(lead)
    return leads


# ── Public entry point ────────────────────────────────────────────────────────
def run_seed(db: Session, company_id: int):
    """Seed all demo/sample data. Returns summary dict."""
    customers = _seed_customers(db, company_id)
    suppliers = _seed_suppliers(db, company_id)
    products  = _seed_products(db, company_id)
    opening   = _seed_opening_stock(db, company_id, products)
    terminal  = _seed_pos_terminal(db, company_id)
    leads     = _seed_demo_leads(db, company_id, customers)
    return {
        "customers": customers,
        "suppliers": suppliers,
        "products":  products,
        "opening_movement": opening,
        "terminal": terminal,
        "leads": leads,
    }
