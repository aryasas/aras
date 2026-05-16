"""
Generate random Inflow and Outflow invoices from real DB data.

Usage:
    python seed_random_invoices.py [--org-id 1] [--count 5] [--post]
"""
import sys
import os
import random
import argparse
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from core.lib.database import SessionLocal
from core.logic import discovery

discovery.discover_apps()

from core import Aras


def random_2025_date() -> date:
    start = date(2025, 1, 1)
    return start + timedelta(days=random.randint(0, 364))


def get_sales_price(db, product_id: int, sales_price_type_ids: list[int]) -> float:
    PriceList = Aras.Model._registry["PriceList"]
    pl = (
        db.query(PriceList)
        .filter(
            PriceList.product_id == product_id,
            PriceList.price_type_id.in_(sales_price_type_ids),
            PriceList.is_active == True,
        )
        .first()
    )
    if pl and pl.price:
        return float(pl.price)
    return 10000.0


def get_purchase_price(db, product_id: int, purchase_price_type_ids: list[int]) -> float:
    PriceList = Aras.Model._registry["PriceList"]
    pl = (
        db.query(PriceList)
        .filter(
            PriceList.product_id == product_id,
            PriceList.price_type_id.in_(purchase_price_type_ids),
            PriceList.is_active == True,
        )
        .first()
    )
    if pl and pl.price:
        return float(pl.price)
    return 8000.0


def make_number(prefix: str, d: date, seq: int) -> str:
    return f"{prefix}/RAND/{d.strftime('%Y%m%d')}/{seq:03d}"


def seed(org_id: int, count: int, do_post: bool):
    db = SessionLocal()
    try:
        Party = Aras.Model._registry["Party"]
        Product = Aras.Model._registry["Product"]
        PriceType = Aras.Model._registry["PriceType"]
        Currency = Aras.Model._registry["Currency"]
        InflowInvoice = Aras.Model._registry["InflowInvoice"]
        InflowInvoiceLine = Aras.Model._registry["InflowInvoiceLine"]
        OutflowInvoice = Aras.Model._registry["OutflowInvoice"]
        OutflowInvoiceLine = Aras.Model._registry["OutflowInvoiceLine"]

        customers = db.query(Party).filter(Party.org_id == org_id, Party.role == "customer").all()
        suppliers = db.query(Party).filter(Party.org_id == org_id, Party.role == "supplier").all()
        products = db.query(Product).filter(Product.org_id == org_id, Product.is_active == True).all()

        if not customers:
            print("No customers found. Seed parties first.")
            return
        if not suppliers:
            print("No suppliers found. Seed parties first.")
            return
        if not products:
            print("No products found. Seed products first.")
            return

        sales_price_type_ids = [
            pt.id for pt in db.query(PriceType).filter(PriceType.kind == "sales").all()
        ]
        purchase_price_type_ids = [
            pt.id for pt in db.query(PriceType).filter(PriceType.kind == "purchase").all()
        ]

        default_currency = db.query(Currency).first()
        currency_id = default_currency.id if default_currency else None

        created_inflow = []
        created_outflow = []

        for i in range(1, count + 1):
            d = random_2025_date()
            number = make_number("SINV", d, i)

            existing = db.query(InflowInvoice).filter(
                InflowInvoice.number == number,
                InflowInvoice.org_id == org_id,
            ).first()
            if existing:
                print(f"  SKIP (exists): {number}")
                continue

            party = random.choice(customers)
            inv = InflowInvoice(
                org_id=org_id,
                number=number,
                doc_date=d,
                party_id=party.id,
                currency_id=currency_id,
                status="Draft",
            )
            db.add(inv)
            db.flush()

            line_products = random.sample(products, min(random.randint(2, 4), len(products)))
            for prod in line_products:
                price = get_sales_price(db, prod.id, sales_price_type_ids)
                db.add(InflowInvoiceLine(
                    invoice_id=inv.id,
                    product_id=prod.id,
                    qty=float(random.randint(1, 10)),
                    unit_price=price,
                    discount=0.0,
                    uom_id=prod.uom_id,
                ))

            db.flush()
            inv.recalc()
            db.flush()
            created_inflow.append(inv)

        for i in range(1, count + 1):
            d = random_2025_date()
            number = make_number("PINV", d, i)

            existing = db.query(OutflowInvoice).filter(
                OutflowInvoice.number == number,
                OutflowInvoice.org_id == org_id,
            ).first()
            if existing:
                print(f"  SKIP (exists): {number}")
                continue

            party = random.choice(suppliers)
            inv = OutflowInvoice(
                org_id=org_id,
                number=number,
                doc_date=d,
                party_id=party.id,
                currency_id=currency_id,
                status="Draft",
            )
            db.add(inv)
            db.flush()

            line_products = random.sample(products, min(random.randint(2, 4), len(products)))
            for prod in line_products:
                price = get_purchase_price(db, prod.id, purchase_price_type_ids)
                db.add(OutflowInvoiceLine(
                    invoice_id=inv.id,
                    product_id=prod.id,
                    qty=float(random.randint(1, 10)),
                    unit_price=price,
                    discount=0.0,
                    uom_id=prod.uom_id,
                ))

            db.flush()
            inv.recalc()
            db.flush()
            created_outflow.append(inv)

        db.commit()

        if do_post:
            for inv in created_inflow + created_outflow:
                try:
                    db.refresh(inv)
                    inv.post()
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"  POST FAILED {inv.number}: {e}")

        print(f"\n{'─'*56}")
        print(f"{'Type':<12} {'Number':<32} {'Total':>10}")
        print(f"{'─'*56}")
        for inv in created_inflow:
            print(f"{'Inflow':<12} {inv.number:<32} {inv.total_amount:>10,.0f}")
        for inv in created_outflow:
            print(f"{'Outflow':<12} {inv.number:<32} {inv.total_amount:>10,.0f}")
        print(f"{'─'*56}")
        print(f"Created: {len(created_inflow)} inflow, {len(created_outflow)} outflow invoices.")
        if do_post:
            print("All invoices posted.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed random invoices")
    parser.add_argument("--org-id", type=int, default=1)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--post", action="store_true")
    args = parser.parse_args()

    seed(args.org_id, args.count, args.post)
