"""
Demo seed: Sales Invoices + Purchase Invoices
Requires demo seed (customers, suppliers, products, COA) to have run first.

Run:
  cd api && python seed_invoices.py [--company-id 1] [--post]

Flags:
  --post     Auto-post all invoices after creation (triggers journal + stock movement)
"""
import sys, os, argparse
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import date
from core import Aras
from core.lib.database import SessionLocal
from core.logic import discovery


def _get(db, model_name, **kw):
    M = Aras.Model._registry[model_name]
    return M.find(db, **kw)


def _uom(db, name):
    return _get(db, "Uom", name=name)


def _seed_sales_invoices(db, company_id: int, do_post: bool):
    SalesInvoice     = Aras.Model._registry["SalesInvoice"]
    SalesInvoiceLine = Aras.Model._registry["SalesInvoiceLine"]
    Customer         = Aras.Model._registry["Customer"]
    Product          = Aras.Model._registry["Product"]
    Currency         = Aras.Model._registry["Currency"]

    pcs = _uom(db, "Pieces")
    idr = _get(db, "Currency", code="IDR")

    # Lookup customers
    c001 = Customer.find(db, company_id=company_id, code="C001")  # Toko Maju Bersama
    c002 = Customer.find(db, company_id=company_id, code="C002")  # CV Sejahtera Abadi
    c003 = Customer.find(db, company_id=company_id, code="C003")  # PT Distribusi Nusa

    # Lookup products
    coffee  = Product.find(db, company_id=company_id, code="P-KOPI-001")
    tea     = Product.find(db, company_id=company_id, code="P-TEH-001")
    water   = Product.find(db, company_id=company_id, code="P-AIR-001")
    snack   = Product.find(db, company_id=company_id, code="P-SNK-001")
    cable   = Product.find(db, company_id=company_id, code="P-CBL-001")

    invoices_data = [
        # (number, customer, doc_date, lines: [(product, qty, unit_price, discount)])
        ("SINV/2025/0001", c001, date(2025, 1, 10), [
            (coffee, 10, 15000, 0),
            (tea,    20,  9000, 0),
        ]),
        ("SINV/2025/0002", c002, date(2025, 1, 15), [
            (water,  50,  3500, 0),
            (snack,  30,  7000, 500),   # 500 discount per unit
        ]),
        ("SINV/2025/0003", c003, date(2025, 2, 3), [
            (coffee, 25, 15000, 1000),
            (cable,   5, 25000,    0),
        ]),
    ]

    results = []
    for number, customer, doc_date, line_defs in invoices_data:
        # Skip if already exists
        existing = SalesInvoice.find(db, company_id=company_id, number=number)
        if existing:
            print(f"  [skip] {number} already exists")
            results.append(existing)
            continue

        if not customer:
            print(f"  [warn] Customer not found for {number}, skipping")
            continue

        inv = SalesInvoice.create(db, {
            "company_id":  company_id,
            "number":      number,
            "customer_id": customer.id,
            "currency_id": idr.id if idr else None,
            "doc_date":    doc_date,
            "status":      "Draft",
            "notes":       f"Demo sales invoice {number}",
        })

        for product, qty, unit_price, discount in line_defs:
            if not product or not pcs:
                continue
            SalesInvoiceLine.create(db, {
                "invoice_id": inv.id,
                "product_id": product.id,
                "qty":        float(qty),
                "uom_id":     pcs.id,
                "unit_price": float(unit_price),
                "discount":   float(discount),
            })

        inv.recalc()
        db.flush()
        print(f"  [ok] Created {number}  total={inv.total_amount:,.0f}")

        if do_post:
            result = inv.post()
            if result is True:
                print(f"       -> Posted. Journal entry + stock movement created.")
            else:
                print(f"       -> Post FAILED: {result}")

        results.append(inv)

    return results


def _seed_purchase_invoices(db, company_id: int, do_post: bool):
    PurchaseInvoice     = Aras.Model._registry["PurchaseInvoice"]
    PurchaseInvoiceLine = Aras.Model._registry["PurchaseInvoiceLine"]
    Supplier            = Aras.Model._registry["Supplier"]
    Product             = Aras.Model._registry["Product"]

    pcs = _uom(db, "Pieces")
    idr = _get(db, "Currency", code="IDR")

    # Lookup suppliers
    s001 = Supplier.find(db, company_id=company_id, code="S001")  # PT Sumber Makmur
    s002 = Supplier.find(db, company_id=company_id, code="S002")  # CV Bahan Prima
    s003 = Supplier.find(db, company_id=company_id, code="S003")  # Importir Asia Jaya

    coffee  = Product.find(db, company_id=company_id, code="P-KOPI-001")
    tea     = Product.find(db, company_id=company_id, code="P-TEH-001")
    sugar   = Product.find(db, company_id=company_id, code="P-GUL-001")
    cable   = Product.find(db, company_id=company_id, code="P-CBL-001")
    charger = Product.find(db, company_id=company_id, code="P-CHR-001")

    kg = _uom(db, "Kilogram")

    invoices_data = [
        # (number, supplier, doc_date, lines: [(product, qty, uom, unit_price, discount)])
        ("PINV/2025/0001", s001, date(2025, 1, 5), [
            (coffee, 50, pcs, 11000, 0),
        ]),
        ("PINV/2025/0002", s002, date(2025, 1, 8), [
            (tea,   100, pcs,  7000, 0),
            (sugar,  20,  kg, 12000, 0),
        ]),
        ("PINV/2025/0003", s003, date(2025, 1, 20), [
            (cable,    15, pcs, 20000, 0),
            (charger,  10, pcs, 90000, 0),
        ]),
    ]

    results = []
    for number, supplier, doc_date, line_defs in invoices_data:
        existing = PurchaseInvoice.find(db, company_id=company_id, number=number)
        if existing:
            print(f"  [skip] {number} already exists")
            results.append(existing)
            continue

        if not supplier:
            print(f"  [warn] Supplier not found for {number}, skipping")
            continue

        inv = PurchaseInvoice.create(db, {
            "company_id":  company_id,
            "number":      number,
            "supplier_id": supplier.id,
            "currency_id": idr.id if idr else None,
            "doc_date":    doc_date,
            "status":      "Draft",
            "notes":       f"Demo purchase invoice {number}",
        })

        for product, qty, uom, unit_price, discount in line_defs:
            if not product or not uom:
                continue
            PurchaseInvoiceLine.create(db, {
                "invoice_id": inv.id,
                "product_id": product.id,
                "qty":        float(qty),
                "uom_id":     uom.id,
                "unit_price": float(unit_price),
                "discount":   float(discount),
            })

        inv.recalc()
        db.flush()
        print(f"  [ok] Created {number}  total={inv.total_amount:,.0f}")

        if do_post:
            result = inv.post()
            if result is True:
                print(f"       -> Posted. Journal entry + stock movement created.")
            else:
                print(f"       -> Post FAILED: {result}")

        results.append(inv)

    return results


def _verify(db, company_id: int):
    """Print summary: invoice totals, journal entries, stock movements."""
    print("\n── Verification ─────────────────────────────────────────")
    from sqlalchemy import text
    rows = db.execute(text(
        "SELECT number, status, total_amount FROM erp_accounting_sales_invoices WHERE company_id=:c ORDER BY number"
    ), {"c": company_id}).fetchall()
    print(f"\nSales Invoices ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  status={r[1]}  total={r[2]:,.0f}")

    rows = db.execute(text(
        "SELECT number, status, total_amount FROM erp_accounting_purchase_invoices WHERE company_id=:c ORDER BY number"
    ), {"c": company_id}).fetchall()
    print(f"\nPurchase Invoices ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  status={r[1]}  total={r[2]:,.0f}")

    rows = db.execute(text(
        "SELECT e.number, e.status, SUM(l.debit) as total_dr, SUM(l.credit) as total_cr "
        "FROM erp_accounting_entries e "
        "JOIN erp_accounting_entry_lines l ON l.entry_id = e.id "
        "WHERE e.company_id=:c GROUP BY e.id ORDER BY e.number"
    ), {"c": company_id}).fetchall()
    print(f"\nJournal Entries ({len(rows)}):")
    for r in rows:
        balanced = "OK" if abs(r[2] - r[3]) < 0.01 else "UNBALANCED!"
        print(f"  {r[0]}  status={r[1]}  DR={r[2]:,.0f}  CR={r[3]:,.0f}  [{balanced}]")

    rows = db.execute(text(
        "SELECT m.number, m.move_type, m.status, COUNT(l.id) as line_count "
        "FROM erp_stock_movements m "
        "LEFT JOIN erp_stock_movement_lines l ON l.movement_id = m.id "
        "WHERE m.company_id=:c AND m.number LIKE 'SM-%%' "
        "GROUP BY m.id ORDER BY m.number"
    ), {"c": company_id}).fetchall()
    print(f"\nAuto Stock Movements ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  type={r[1]}  status={r[2]}  lines={r[3]}")

    print("\n─────────────────────────────────────────────────────────\n")


def main():
    parser = argparse.ArgumentParser(description="Seed demo invoices")
    parser.add_argument("--company-id", type=int, default=1)
    parser.add_argument("--post", action="store_true", help="Auto-post all invoices")
    args = parser.parse_args()

    discovery.discover_apps()

    db = SessionLocal()

    try:
        Company = Aras.Model._registry.get("Company")
        company = db.get(Company, args.company_id) if Company else None
        if not company:
            print(f"Company id={args.company_id} not found. Run manage.py seed first.")
            sys.exit(1)

        print(f"\nCompany: {company.name}  (perpetual_inventory={company.enable_perpetual_inventory})")

        print("\n── Sales Invoices ───────────────────────────────────────")
        _seed_sales_invoices(db, args.company_id, args.post)

        print("\n── Purchase Invoices ────────────────────────────────────")
        _seed_purchase_invoices(db, args.company_id, args.post)

        _verify(db, args.company_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
