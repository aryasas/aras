"""
Test seed: products with UOMs + prices → outflow invoice (stock in + journal) → inflow invoice (stock out + journal).
Run from api/: python seed_test.py
"""
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lib.database import SessionLocal
from core import Aras
from core.logic import discovery


def run():
    print("Discovering apps...")
    discovery.discover_apps(package_path="apps")
    db = SessionLocal()

    try:
        R = Aras.Model._registry

        Organization = R["Organization"]
        hq = db.query(Organization).filter_by(code="HQ").first()
        if not hq:
            print("ERROR: Run seed_basic.py first.")
            return

        Uom = R["Uom"]
        uom_unit = db.query(Uom).filter_by(code="Unit").first()
        uom_box  = db.query(Uom).filter_by(code="Box").first()

        ProductCategory = R["ProductCategory"]
        cat = db.query(ProductCategory).filter_by(code="CAT-GEN", org_id=hq.id).first()

        PriceType = R["PriceType"]
        pt_sales = db.query(PriceType).filter_by(code="SLS-STD").first()
        pt_purch = db.query(PriceType).filter_by(code="PUR-STD").first()

        if not all([uom_unit, cat, pt_sales, pt_purch]):
            print("ERROR: Missing UOM/Category/PriceType — run seed_basic.py first.")
            return

        print("\n[1] Seeding products...")
        Product    = R["Product"]
        ProductUom = R["ProductUom"]
        PriceList  = R["PriceList"]

        products_spec = [
            ("Widget A", "W-001", uom_unit.id, 50_000,  40_000),
            ("Widget B", "W-002", uom_unit.id, 120_000, 90_000),
            ("Gadget C", "G-001", uom_unit.id, 350_000, 280_000),
        ]

        created_products = {}
        for name, code, base_uom, sp, pp in products_spec:
            p, created = Product.get_or_create(
                db,
                {"name": name, "category_id": cat.id, "uom_id": base_uom, "is_active": True},
                org_id=hq.id, code=code
            )
            created_products[code] = p

            if created:
                PriceList.create(db, {
                    "org_id": hq.id, "code": f"PL-{code}-SLS", "name": f"Sales - {name}",
                    "price_type_id": pt_sales.id, "product_id": p.id,
                    "uom_id": base_uom, "price": sp, "is_active": True
                })
                PriceList.create(db, {
                    "org_id": hq.id, "code": f"PL-{code}-PUR", "name": f"Purchase - {name}",
                    "price_type_id": pt_purch.id, "product_id": p.id,
                    "uom_id": base_uom, "price": pp, "is_active": True
                })
                if code == "W-001" and uom_box:
                    ProductUom.create(db, {
                        "code": f"{code}-BOX", "name": f"{name} (Box/12)",
                        "product_id": p.id, "uom_id": uom_box.id,
                        "factor": 12.0, "org_id": hq.id
                    })
                    PriceList.create(db, {
                        "org_id": hq.id, "code": f"PL-{code}-BOX", "name": f"Sales Box - {name}",
                        "price_type_id": pt_sales.id, "product_id": p.id,
                        "uom_id": uom_box.id, "price": sp * 11.0, "is_active": True
                    })

            print(f"  {'Created' if created else 'Exists '}: {name} ({code})")

        db.commit()

        print("\n[2] UOM conversion test (Widget A)...")
        from apps.stock.services.uom import UomService
        wa = created_products["W-001"]
        if uom_box:
            converted = UomService.convert_qty(db, wa.id, qty=2, from_uom_id=uom_box.id, to_uom_id=uom_unit.id)
            print(f"  2 Boxes → {converted} Units (expected 24)")

        print("\n[3] Seeding parties...")
        Party = R["Party"]
        sup, _ = Party.get_or_create(
            db, {"name": "Test Supplier", "contact_email": "sup@test.com", "role": "supplier"},
            org_id=hq.id, code="SUP-TEST"
        )
        cust, _ = Party.get_or_create(
            db, {"name": "Test Customer", "contact_email": "cust@test.com", "role": "customer"},
            org_id=hq.id, code="CUST-TEST"
        )
        db.commit()
        print(f"  Supplier: {sup.name} | Customer: {cust.name}")

        print("\n[4] Creating outflow invoice...")
        OutflowInvoice     = R["OutflowInvoice"]
        OutflowInvoiceLine = R["OutflowInvoiceLine"]

        pinv = OutflowInvoice(
            org_id=hq.id,
            number="PINV-TEST-001",
            party_id=sup.id,
            currency_id=hq.base_currency_id,
            status="Draft",
        )
        db.add(pinv)
        db.flush()

        pinv_lines = [
            (created_products["W-001"], 10, uom_unit.id, 40_000),
            (created_products["W-002"], 5,  uom_unit.id, 90_000),
            (created_products["G-001"], 3,  uom_unit.id, 280_000),
        ]
        for prod, qty, uom_id, unit_price in pinv_lines:
            db.add(OutflowInvoiceLine(
                invoice_id=pinv.id, product_id=prod.id,
                qty=qty, uom_id=uom_id, unit_price=unit_price, discount=0
            ))

        db.flush()
        pinv.recalc()
        db.commit()
        print(f"  Outflow Invoice: {pinv.number} | Total: {pinv.total_amount:,.0f}")

        print("  Posting outflow invoice...")
        from apps.accounting.services.posting import InvoicePostingService
        result = InvoicePostingService.post_outflow_invoice(db, pinv)
        if result is True:
            print(f"  ✓ Posted | Status: {pinv.status}")
        else:
            print(f"  ✗ Error: {result}")
            return

        print("\n[5] Stock on hand after outflow:")
        from apps.stock.services.stock import StockComputeService
        for code, prod in created_products.items():
            qty = StockComputeService.compute_qty(db, prod.id)
            print(f"  {code} ({prod.name}): {qty} units on hand")

        print("\n[6] Creating inflow invoice...")
        InflowInvoice     = R["InflowInvoice"]
        InflowInvoiceLine = R["InflowInvoiceLine"]

        sinv = InflowInvoice(
            org_id=hq.id,
            number="SINV-TEST-001",
            party_id=cust.id,
            currency_id=hq.base_currency_id,
            status="Draft",
        )
        db.add(sinv)
        db.flush()

        sinv_lines = [
            (created_products["W-001"], 4,  uom_unit.id, 50_000),
            (created_products["W-002"], 2,  uom_unit.id, 120_000),
            (created_products["G-001"], 1,  uom_unit.id, 350_000),
        ]
        for prod, qty, uom_id, unit_price in sinv_lines:
            db.add(InflowInvoiceLine(
                invoice_id=sinv.id, product_id=prod.id,
                qty=qty, uom_id=uom_id, unit_price=unit_price, discount=0
            ))

        db.flush()
        sinv.recalc()
        db.commit()
        print(f"  Inflow Invoice: {sinv.number} | Total: {sinv.total_amount:,.0f}")

        print("  Posting inflow invoice...")
        result = InvoicePostingService.post_inflow_invoice(db, sinv)
        if result is True:
            print(f"  ✓ Posted | Status: {sinv.status}")
        else:
            print(f"  ✗ Error: {result}")
            return

        print("\n[7] Stock on hand after inflow:")
        for code, prod in created_products.items():
            qty = StockComputeService.compute_qty(db, prod.id)
            print(f"  {code} ({prod.name}): {qty} units on hand")

        print("\n[8] Journal entries created:")
        JournalEntry     = R["JournalEntry"]
        Account          = R["Account"]

        for ref in [pinv.number, sinv.number]:
            je = db.query(JournalEntry).filter_by(org_id=hq.id, number=ref).first()
            if not je:
                print(f"  {ref}: NO JOURNAL ENTRY FOUND")
                continue
            print(f"\n  ── {ref} (JE #{je.id}) ──")
            for jel in je.lines:
                acc = db.get(Account, jel.account_id)
                acc_name = acc.name if acc else f"#{jel.account_id}"
                dr = f"DR {jel.debit:>12,.0f}" if jel.debit else " " * 20
                cr = f"CR {jel.credit:>12,.0f}" if jel.credit else ""
                print(f"    {acc_name:<30} {dr}  {cr}")

        print("\n[9] Stock movements created:")
        StockMovement     = R["StockMovement"]

        for ref in [f"SM-{pinv.number}", f"SM-{sinv.number}"]:
            sm = db.query(StockMovement).filter_by(org_id=hq.id, number=ref).first()
            if not sm:
                print(f"  {ref}: NOT FOUND")
                continue
            print(f"\n  ── {ref} ({sm.move_type}) ──")
            for sml in sm.lines:
                prod = db.get(Product, sml.product_id)
                print(f"    {prod.name:<25} qty={sml.qty:<8} cost={sml.unit_cost:,.0f}")

        print("\n✓ All tests complete.")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    run()
