"""
Demo seed: Inflow Invoices + Outflow Invoices
Requires demo seed (parties, products, COA) to have run first.

Run:
  cd api && python seed_invoices.py [--org-id 1] [--post]

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


def _seed_inflow_invoices(db, org_id: int, do_post: bool):
    InflowInvoice     = Aras.Model._registry["InflowInvoice"]
    InflowInvoiceLine = Aras.Model._registry["InflowInvoiceLine"]
    Party             = Aras.Model._registry["Party"]
    Product           = Aras.Model._registry["Product"]

    pcs = _uom(db, "Pieces")
    idr = _get(db, "Currency", code="IDR")

    c001 = Party.find(db, org_id=org_id, code="C001")
    c002 = Party.find(db, org_id=org_id, code="C002")
    c003 = Party.find(db, org_id=org_id, code="C003")

    coffee  = Product.find(db, org_id=org_id, code="P-KOPI-001")
    tea     = Product.find(db, org_id=org_id, code="P-TEH-001")
    water   = Product.find(db, org_id=org_id, code="P-AIR-001")
    snack   = Product.find(db, org_id=org_id, code="P-SNK-001")
    cable   = Product.find(db, org_id=org_id, code="P-CBL-001")

    invoices_data = [
        ("SINV/2025/0001", c001, date(2025, 1, 10), [
            (coffee, 10, 15000, 0),
            (tea,    20,  9000, 0),
        ]),
        ("SINV/2025/0002", c002, date(2025, 1, 15), [
            (water,  50,  3500, 0),
            (snack,  30,  7000, 500),
        ]),
        ("SINV/2025/0003", c003, date(2025, 2, 3), [
            (coffee, 25, 15000, 1000),
            (cable,   5, 25000,    0),
        ]),
    ]

    results = []
    for number, party, doc_date, line_defs in invoices_data:
        existing = InflowInvoice.find(db, org_id=org_id, number=number)
        if existing:
            print(f"  [skip] {number} already exists")
            results.append(existing)
            continue

        if not party:
            print(f"  [warn] Party not found for {number}, skipping")
            continue

        inv = InflowInvoice.create(db, {
            "org_id":      org_id,
            "number":      number,
            "party_id":    party.id,
            "currency_id": idr.id if idr else None,
            "doc_date":    doc_date,
            "status":      "Draft",
            "notes":       f"Demo inflow invoice {number}",
        })

        for product, qty, unit_price, discount in line_defs:
            if not product or not pcs:
                continue
            InflowInvoiceLine.create(db, {
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


def _seed_outflow_invoices(db, org_id: int, do_post: bool):
    OutflowInvoice     = Aras.Model._registry["OutflowInvoice"]
    OutflowInvoiceLine = Aras.Model._registry["OutflowInvoiceLine"]
    Party              = Aras.Model._registry["Party"]
    Product            = Aras.Model._registry["Product"]

    pcs = _uom(db, "Pieces")
    idr = _get(db, "Currency", code="IDR")

    s001 = Party.find(db, org_id=org_id, code="S001")
    s002 = Party.find(db, org_id=org_id, code="S002")
    s003 = Party.find(db, org_id=org_id, code="S003")

    coffee  = Product.find(db, org_id=org_id, code="P-KOPI-001")
    tea     = Product.find(db, org_id=org_id, code="P-TEH-001")
    sugar   = Product.find(db, org_id=org_id, code="P-GUL-001")
    cable   = Product.find(db, org_id=org_id, code="P-CBL-001")
    charger = Product.find(db, org_id=org_id, code="P-CHR-001")

    kg = _uom(db, "Kilogram")

    invoices_data = [
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
    for number, party, doc_date, line_defs in invoices_data:
        existing = OutflowInvoice.find(db, org_id=org_id, number=number)
        if existing:
            print(f"  [skip] {number} already exists")
            results.append(existing)
            continue

        if not party:
            print(f"  [warn] Party not found for {number}, skipping")
            continue

        inv = OutflowInvoice.create(db, {
            "org_id":      org_id,
            "number":      number,
            "party_id":    party.id,
            "currency_id": idr.id if idr else None,
            "doc_date":    doc_date,
            "status":      "Draft",
            "notes":       f"Demo outflow invoice {number}",
        })

        for product, qty, uom, unit_price, discount in line_defs:
            if not product or not uom:
                continue
            OutflowInvoiceLine.create(db, {
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


def _verify(db, org_id: int):
    print("\n── Verification ─────────────────────────────────────────")
    from sqlalchemy import text
    rows = db.execute(text(
        "SELECT number, status, total_amount FROM erp_accounting_inflow_invoices WHERE org_id=:c ORDER BY number"
    ), {"c": org_id}).fetchall()
    print(f"\nInflow Invoices ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  status={r[1]}  total={r[2]:,.0f}")

    rows = db.execute(text(
        "SELECT number, status, total_amount FROM erp_accounting_outflow_invoices WHERE org_id=:c ORDER BY number"
    ), {"c": org_id}).fetchall()
    print(f"\nOutflow Invoices ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  status={r[1]}  total={r[2]:,.0f}")

    rows = db.execute(text(
        "SELECT e.number, e.status, SUM(l.debit) as total_dr, SUM(l.credit) as total_cr "
        "FROM erp_accounting_entries e "
        "JOIN erp_accounting_entry_lines l ON l.entry_id = e.id "
        "WHERE e.org_id=:c GROUP BY e.id ORDER BY e.number"
    ), {"c": org_id}).fetchall()
    print(f"\nJournal Entries ({len(rows)}):")
    for r in rows:
        balanced = "OK" if abs(r[2] - r[3]) < 0.01 else "UNBALANCED!"
        print(f"  {r[0]}  status={r[1]}  DR={r[2]:,.0f}  CR={r[3]:,.0f}  [{balanced}]")

    rows = db.execute(text(
        "SELECT m.number, m.move_type, m.status, COUNT(l.id) as line_count "
        "FROM erp_stock_movements m "
        "LEFT JOIN erp_stock_movement_lines l ON l.movement_id = m.id "
        "WHERE m.org_id=:c AND m.number LIKE 'SM-%%' "
        "GROUP BY m.id ORDER BY m.number"
    ), {"c": org_id}).fetchall()
    print(f"\nAuto Stock Movements ({len(rows)}):")
    for r in rows:
        print(f"  {r[0]}  type={r[1]}  status={r[2]}  lines={r[3]}")

    print("\n─────────────────────────────────────────────────────────\n")


def main():
    parser = argparse.ArgumentParser(description="Seed demo invoices")
    parser.add_argument("--org-id", type=int, default=1)
    parser.add_argument("--post", action="store_true", help="Auto-post all invoices")
    args = parser.parse_args()

    discovery.discover_apps()

    db = SessionLocal()

    try:
        Organization = Aras.Model._registry.get("Organization")
        org = db.get(Organization, args.org_id) if Organization else None
        if not org:
            print(f"Organization id={args.org_id} not found. Run manage.py seed first.")
            sys.exit(1)

        print(f"\nOrganization: {org.name}  (perpetual_inventory={org.enable_perpetual_inventory})")

        print("\n── Inflow Invoices ──────────────────────────────────────")
        _seed_inflow_invoices(db, args.org_id, args.post)

        print("\n── Outflow Invoices ─────────────────────────────────────")
        _seed_outflow_invoices(db, args.org_id, args.post)

        _verify(db, args.org_id)
    finally:
        db.close()


if __name__ == "__main__":
    main()
