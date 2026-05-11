"""Demo data seed — idempotent.

Requires standard seed to have run first (CoA, UoMs, warehouses, payment modes,
customer/supplier groups, price types, fiscal year, doc series).

Covers: customers, suppliers, products (stockable + service + bundle),
UoM conversions, price lists, opening stock movements.

Entry point: run_seed(company_id) → dict of created objects.
"""
from decimal import Decimal
from arasCore.lib.core.extensions import db


# ── helpers ───────────────────────────────────────────────────────────────────
def _uom(name):
    from app.erp.erp_stock.models.uom import StockUom
    return StockUom.find(name=name)


def _category(name):
    from app.erp.erp_stock.models.product import StockProductCategory
    return StockProductCategory.find(name=name)


def _price_type(company_id, name):
    from app.erp.erp_config.models.price_type import StockPriceType
    return StockPriceType.find(company_id=company_id, name=name)


def _location(company_id, name):
    from app.erp.erp_stock.models.warehouse import StockLocation
    return StockLocation.find(company_id=company_id, name=name)


def _currency(code):
    from app.erp.erp_config.models.currency import Currency
    return Currency.find(code=code)


# ── Customers ─────────────────────────────────────────────────────────────────
_CUSTOMERS = [
    # (code, name, group_name, phone, email)
    ("C001", "Toko Maju Bersama",   "Retail",      "0812-0001-0001", "toko.maju@example.com"),
    ("C002", "CV Sejahtera Abadi",  "Wholesale",   "0812-0002-0002", "sejahtera@example.com"),
    ("C003", "PT Distribusi Nusa",  "Distributor", "0812-0003-0003", "distribusi@example.com"),
    ("C004", "Warung Pak Budi",     "Retail",      "0812-0004-0004", None),
    ("C005", "Koperasi Karyawan",   "Government",  "0812-0005-0005", "koperasi@example.com"),
]

def _seed_customers(company_id):
    from app.erp.erp_crm.models.customer import CrmCustomer
    from app.erp.erp_crm.models.customer_group import CrmCustomerGroup
    idr = _currency("IDR")
    out = {}
    for code, name, group_name, phone, email in _CUSTOMERS:
        group = CrmCustomerGroup.find(name=group_name)
        obj, _ = CrmCustomer.get_or_create(
            {
                "name": name,
                "group_id": group.id if group else None,
                "currency_id": idr.id if idr else None,
                "phone": phone,
                "email": email,
                "is_active": True,
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

def _seed_suppliers(company_id):
    from app.erp.erp_sup.models.supplier import SupSupplier
    from app.erp.erp_sup.models.supplier_group import SupSupplierGroup
    idr = _currency("IDR")
    out = {}
    for code, name, group_name, phone, email in _SUPPLIERS:
        group = SupSupplierGroup.find(name=group_name)
        obj, _ = SupSupplier.get_or_create(
            {
                "name": name,
                "group_id": group.id if group else None,
                "currency_id": idr.id if idr else None,
                "phone": phone,
                "email": email,
                "is_active": True,
            },
            company_id=company_id, code=code,
        )
        out[code] = obj
    return out


# ── Products ──────────────────────────────────────────────────────────────────
def _seed_products(company_id):
    from app.erp.erp_stock.models.product import (
        StockProduct, StockProductUom, StockPriceList, StockProductBundle,
    )
    idr = _currency("IDR")
    pcs = _uom("Pcs")
    box = _uom("Box")
    ctn = _uom("Carton")
    kg  = _uom("Kilogram")
    g   = _uom("Gram")
    ltr = _uom("Liter")
    ml  = _uom("Milliliter")

    cat_fnb   = _category("Food & Beverage")
    cat_elec  = _category("Electronics")
    cat_svc   = _category("Services")
    cat_raw   = _category("Raw Materials")

    pt_sell = _price_type(company_id, "Standard Selling")
    pt_buy  = _price_type(company_id, "Standard Buying")

    out = {}

    def _make(code, name, cat, uom, for_sales, for_purchase, is_stock, sell_price, buy_price, sell_uom=None):
        prod, _ = StockProduct.get_or_create(
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
            StockPriceList.get_or_create(
                {"price": Decimal(str(sell_price)), "min_qty": 1,
                 "uom_id": suom.id, "is_active": True,
                 "currency_id": idr.id if idr else None},
                product_id=prod.id, price_type_id=pt_sell.id, uom_id=suom.id,
            )
        if pt_buy and buy_price is not None:
            StockPriceList.get_or_create(
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
        StockProductUom.get_or_create(
            {"factor": Decimal("12"), "is_active": True},
            product_id=coffee.id, uom_id=box.id,
        )
    if ctn:
        StockProductUom.get_or_create(
            {"factor": Decimal("144"), "is_active": True},
            product_id=coffee.id, uom_id=ctn.id,
        )
    # Tea: Box = 24 Pcs
    if box:
        StockProductUom.get_or_create(
            {"factor": Decimal("24"), "is_active": True},
            product_id=tea.id, uom_id=box.id,
        )
    # Sugar: Gram = 0.001 Kg
    if g:
        StockProductUom.get_or_create(
            {"factor": Decimal("0.001"), "is_active": True},
            product_id=sugar.id, uom_id=g.id,
        )
    # Syrup: 650 ml per bottle (base Liter → Milliliter)
    if ml and ltr:
        StockProductUom.get_or_create(
            {"factor": Decimal("0.001"), "is_active": True},
            product_id=syrup.id, uom_id=ml.id,
        )
    # Water: Box = 24 Pcs
    if box:
        StockProductUom.get_or_create(
            {"factor": Decimal("24"), "is_active": True},
            product_id=water.id, uom_id=box.id,
        )
    # Snack: Box = 20 Pcs, Carton = 200 Pcs
    if box:
        StockProductUom.get_or_create(
            {"factor": Decimal("20"), "is_active": True},
            product_id=snack.id, uom_id=box.id,
        )
    if ctn:
        StockProductUom.get_or_create(
            {"factor": Decimal("200"), "is_active": True},
            product_id=snack.id, uom_id=ctn.id,
        )

    # ── Price breaks (wholesale — box pricing) ────────────────────────────────
    if pt_sell and box and idr:
        StockPriceList.get_or_create(
            {"price": Decimal("300000"), "min_qty": 1, "uom_id": box.id,
             "is_active": True, "currency_id": idr.id},
            product_id=coffee.id, price_type_id=pt_sell.id, uom_id=box.id,
        )

    # ── Bundle: Coffee Starter Pack = 1 Coffee + 1 Tea + 1 Sugar ─────────────
    bundle = _make("P-BSP-001", "Coffee Starter Pack", cat_fnb, pcs, True, False, False, 55000, None)
    StockProductBundle.get_or_create(
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=bundle.id, component_id=coffee.id,
    )
    StockProductBundle.get_or_create(
        {"qty": Decimal("1"), "uom_id": pcs.id},
        bundle_id=bundle.id, component_id=tea.id,
    )
    StockProductBundle.get_or_create(
        {"qty": Decimal("1"), "uom_id": kg.id},
        bundle_id=bundle.id, component_id=sugar.id,
    )
    out["bundle_starter"] = bundle

    return out


# ── Opening Stock ─────────────────────────────────────────────────────────────
def _seed_opening_stock(company_id, products):
    """Create a single opening-stock movement (state=draft, not posted).
    This gives the demo something to look at without triggering valuation logic.
    """
    from app.erp.erp_stock.models.movement import StockMovement, StockMovementLine

    loc = _location(company_id, "Stock Shelf") or _location(company_id, "Main Warehouse")
    if not loc:
        return None

    pcs = _uom("Pcs")
    kg  = _uom("Kilogram")

    # Only seed if no opening movement exists yet
    existing = StockMovement.find(company_id=company_id, move_type="opening")
    if existing:
        return existing

    from datetime import date
    mv = StockMovement.create({
        "company_id":      company_id,
        "name":            "OPEN/DEMO/001",
        "move_type":       "opening",
        "state":           "draft",
        "date_move":       date.today(),
        "dst_location_id": loc.id,
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
        StockMovementLine.create({
            "movement_id":  mv.id,
            "product_id":   prod.id,
            "qty":          Decimal(str(qty)),
            "qty_base":     Decimal(str(qty)),
            "uom_id":       uom.id,
            "unit_cost":    Decimal(str(cost)),
            "dst_location_id": loc.id,
        })
    return mv


# ── POS Terminal ──────────────────────────────────────────────────────────────
def _seed_pos_terminal(company_id):
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_main.models.payment_mode import ModeOfPayment

    loc = _location(company_id, "POS Counter") or _location(company_id, "Store")
    cash_mop = ModeOfPayment.find(name="Cash")

    terminal, _ = PosTerminal.get_or_create(
        {
            "name": "Kasir Utama",
            "location_id": loc.id if loc else None,
            "default_mop_id": cash_mop.id if cash_mop else None,
            "is_active": True,
        },
        company_id=company_id, code="K1",
    )
    return terminal


# ── CRM Demo Leads ────────────────────────────────────────────────────────────
def _seed_demo_leads(company_id, customers):
    from app.erp.erp_crm.models.lead import CrmLead
    from app.erp.erp_crm.models.pipeline import CrmPipeline, CrmStage

    pipeline = CrmPipeline.find(name="Sales Pipeline")
    if not pipeline:
        return []

    stage_new  = CrmStage.find(pipeline_id=pipeline.id, name="New Lead")
    stage_qual = CrmStage.find(pipeline_id=pipeline.id, name="Qualified")
    stage_prop = CrmStage.find(pipeline_id=pipeline.id, name="Proposal Sent")

    leads_data = [
        ("Penawaran Kopi Arabica",     customers.get("C001"), stage_new),
        ("Proposal Grosir Minuman",    customers.get("C002"), stage_qual),
        ("Follow-up Distributor Nusa", customers.get("C003"), stage_prop),
    ]
    leads = []
    for name, customer, stage in leads_data:
        lead, _ = CrmLead.get_or_create(
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
def run_seed(company_id):
    """Seed all demo/sample data. Returns summary dict."""
    customers = _seed_customers(company_id)
    suppliers = _seed_suppliers(company_id)
    products  = _seed_products(company_id)
    opening   = _seed_opening_stock(company_id, products)
    terminal  = _seed_pos_terminal(company_id)
    leads     = _seed_demo_leads(company_id, customers)
    db.session.commit()
    return {
        "customers": customers,
        "suppliers": suppliers,
        "products":  products,
        "opening_movement": opening,
        "terminal": terminal,
        "leads": leads,
    }
