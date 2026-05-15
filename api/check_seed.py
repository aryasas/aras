import sys
import os

# Add 'api' directory to path so 'core' is discoverable as a top-level package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lib.database import SessionLocal
from core import Aras
from core.logic import discovery

def check_data():
    discovery.discover_apps(package_path="apps")
    db = SessionLocal()
    try:
        Product = Aras.Model._registry["Product"]
        PriceList = Aras.Model._registry["PriceList"]
        ProductUom = Aras.Model._registry["ProductUom"]
        Uom = Aras.Model._registry["Uom"]

        products = db.query(Product).all()
        print(f"Total Products: {len(products)}")
        for p in products:
            print(f" - {p.name} ({p.code}), Price: {p.price}, Base UOM: {p.uom_id}")
            
            # Check Pricelists
            prices = db.query(PriceList).filter_by(product_id=p.id).all()
            print(f"   Prices: {len(prices)}")
            for pr in prices:
                print(f"     * {pr.name}: {pr.price} per UOM ID {pr.uom_id}")
            
            # Check ProductUoms
            uoms = db.query(ProductUom).filter_by(product_id=p.id).all()
            print(f"   Alt Units: {len(uoms)}")
            for pu in uoms:
                uom_name = db.query(Uom).get(pu.uom_id).name if pu.uom_id else "N/A"
                print(f"     * {uom_name}: factor {pu.factor}")

    finally:
        db.close()

if __name__ == "__main__":
    check_data()
