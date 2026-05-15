"""
Generate random Sales and Purchase invoices from real DB data.

Usage:
    python seed_random_invoices.py [--company-id 1] [--count 5] [--post]
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


def seed(company_id: int, count: int, do_post: bool):
    db = SessionLocal()
    try:
        Customer = Aras.Model._registry["Customer"]
        Supplier = Aras.Model._registry["Supplier"]
        Product = Aras.Model._registry["Product"]
        PriceType = Aras.Model._registry["PriceType"]
        Currency = Aras.Model._registry["Currency"]
        SalesInvoice = Aras.Model._registry["SalesInvoice"]
        SalesInvoiceLine = Aras.Model._registry["SalesInvoiceLine"]
        PurchaseInvoice = Aras.Model._registry["PurchaseInvoice"]
        PurchaseInvoiceLine = Aras.Model._registry["PurchaseInvoiceLine"]

        customers = db.query(Customer).filter(Customer.company_id == company_id).all()
        suppliers = db.query(Supplier).filter(Supplier.company_id == company_id).all()
        products = db.query(Product).filter(Product.company_id == company_id, Product.is_active == True).all()

        if not customers:
            print("No customers found. Seed customers first.")
            return
        if not suppliers:
            print("No suppliers found. Seed suppliers first.")
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

        sales_products = [p for p in products] or products
        purchase_products = [p for p in products] or products

        created_sales = []
        created_purchase = []

        # Sales invoices
        for i in range(1, count + 1):
            d = random_2025_date()
            number = make_number("SINV", d, i)

            existing = db.query(SalesInvoice).filter(
                SalesInvoice.number == number,
                SalesInvoice.company_id == company_id,
            ).first()
            if existing:
                print(f"  SKIP (exists): {number}")
                continue

            customer = random.choice(customers)
            inv = SalesInvoice(
                company_id=company_id,
                number=number,
                doc_date=d,
                customer_id=customer.id,
                currency_id=currency_id,
                status="Draft",
            )
            db.add(inv)
            db.flush()

            line_products = random.sample(sales_products, min(random.randint(2, 4), len(sales_products)))
            for prod in line_products:
                price = get_sales_price(db, prod.id, sales_price_type_ids)
                line = SalesInvoiceLine(
                    invoice_id=inv.id,
                    product_id=prod.id,
                    qty=float(random.randint(1, 10)),
                    unit_price=price,
                    discount=0.0,
                    uom_id=prod.uom_id,
                )
                db.add(line)

            db.flush()
            inv.recalc()
            db.flush()
            created_sales.append(inv)

        # Purchase invoices
        for i in range(1, count + 1):
            d = random_2025_date()
            number = make_number("PINV", d, i)

            existing = db.query(PurchaseInvoice).filter(
                PurchaseInvoice.number == number,
                PurchaseInvoice.company_id == company_id,
            ).first()
            if existing:
                print(f"  SKIP (exists): {number}")
                continue

            supplier = random.choice(suppliers)
            inv = PurchaseInvoice(
                company_id=company_id,
                number=number,
                doc_date=d,
                supplier_id=supplier.id,
                currency_id=currency_id,
                status="Draft",
            )
            db.add(inv)
            db.flush()

            line_products = random.sample(purchase_products, min(random.randint(2, 4), len(purchase_products)))
            for prod in line_products:
                price = get_purchase_price(db, prod.id, purchase_price_type_ids)
                line = PurchaseInvoiceLine(
                    invoice_id=inv.id,
                    product_id=prod.id,
                    qty=float(random.randint(1, 10)),
                    unit_price=price,
                    discount=0.0,
                    uom_id=prod.uom_id,
                )
                db.add(line)

            db.flush()
            inv.recalc()
            db.flush()
            created_purchase.append(inv)

        db.commit()

        if do_post:
            for inv in created_sales + created_purchase:
                try:
                    db.refresh(inv)
                    inv.post()
                    db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"  POST FAILED {inv.number}: {e}")

        # Summary
        print(f"\n{'─'*56}")
        print(f"{'Type':<12} {'Number':<32} {'Total':>10}")
        print(f"{'─'*56}")
        for inv in created_sales:
            print(f"{'Sales':<12} {inv.number:<32} {inv.total_amount:>10,.0f}")
        for inv in created_purchase:
            print(f"{'Purchase':<12} {inv.number:<32} {inv.total_amount:>10,.0f}")
        print(f"{'─'*56}")
        print(f"Created: {len(created_sales)} sales, {len(created_purchase)} purchase invoices.")
        if do_post:
            print("All invoices posted.")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed random invoices")
    parser.add_argument("--company-id", type=int, default=1)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--post", action="store_true")
    args = parser.parse_args()

    seed(args.company_id, args.count, args.post)
