import sys
import os

# Add 'api' directory to path so 'core' is discoverable as a top-level package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lib.database import SessionLocal
from core import Aras
from core.logic import discovery

def seed_products():
    print("Discovering apps and registering models...")
    discovery.discover_apps(package_path="apps")

    db = SessionLocal()
    try:
        # Lookup required records
        Company = Aras.Model._registry["Organization"]
        Uom = Aras.Model._registry["Uom"]
        ProductCategory = Aras.Model._registry["ProductCategory"]
        PriceType = Aras.Model._registry["PriceType"]
        Product = Aras.Model._registry["Product"]
        ProductUom = Aras.Model._registry["ProductUom"]
        PriceList = Aras.Model._registry["PriceList"]

        hq = db.query(Company).filter_by(code="HQ").first()
        if not hq:
            print("HQ Company not found. Please run seed_basic.py first.")
            return

        uom_unit = db.query(Uom).filter_by(code="Unit").first()
        uom_box = db.query(Uom).filter_by(code="Box").first()
        cat_gen = db.query(ProductCategory).filter_by(code="CAT-GEN").first()
        pt_sales = db.query(PriceType).filter_by(code="SLS-STD").first()

        if not all([uom_unit, cat_gen, pt_sales]):
            print("Required basic data (UOM, Category, PriceType) missing. Please run seed_basic.py first.")
            return

        # 1. Create Products
        print("Seeding Products...")
        products_data = [
            ("Smartphone X", "PROD-001", 5000000),
            ("Laptop Pro", "PROD-002", 15000000),
            ("Wireless Earbuds", "PROD-003", 750000),
        ]

        for name, code, price in products_data:
            p, created = Product.get_or_create(
                db,
                {
                    "name": name,
                    "category_id": cat_gen.id,
                    "uom_id": uom_unit.id,
                    "is_active": True,
                },
                org_id=hq.id, code=code
            )
            
            if created:
                # Add PriceList entry
                print(f"  Adding price for {name}...")
                PriceList.create(db, {
                    "org_id": hq.id,
                    "code": f"PR-{code}",
                    "name": f"Standard Price - {name}",
                    "price_type_id": pt_sales.id,
                    "product_id": p.id,
                    "uom_id": uom_unit.id,
                    "price": price,
                    "is_active": True
                })

                # For the laptop, let's add an alternate UOM (Box of 5)
                if code == "PROD-002" and uom_box:
                    print(f"  Adding alternate UOM for {name}...")
                    ProductUom.create(db, {
                        "code": f"{code}-BOX",
                        "name": f"{name} Box",
                        "product_id": p.id,
                        "uom_id": uom_box.id,
                        "factor": 5.0,
                        "org_id": hq.id
                    })
                    
                    # Also add a price for the box (slightly discounted)
                    PriceList.create(db, {
                        "org_id": hq.id,
                        "code": f"PR-{code}-BOX",
                        "name": f"Box Price - {name}",
                        "price_type_id": pt_sales.id,
                        "product_id": p.id,
                        "uom_id": uom_box.id,
                        "price": price * 4.8, # 5 units for the price of 4.8
                        "is_active": True
                    })

        db.commit()
        print("Product data seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding product data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_products()
