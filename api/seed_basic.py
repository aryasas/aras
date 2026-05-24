import sys
import os

# Add 'api' directory to path so 'core' is discoverable as a top-level package
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.lib.database import SessionLocal
from core import Aras
from core.logic import discovery
from apps.accounting.seed_coa import seed_coa

def seed_basic_data():
    print("Discovering apps and registering models...")
    discovery.discover_apps(package_path="apps")

    db = SessionLocal()
    try:
        # 1. Seed Currencies
        print("Seeding Currencies...")
        Currency = Aras.Model._registry["Currency"]
        idr, _ = Currency.get_or_create(db, {"name": "Indonesian Rupiah", "symbol": "Rp"}, code="IDR")
        usd, _ = Currency.get_or_create(db, {"name": "US Dollar", "symbol": "$"}, code="USD")
        db.commit()

        # 2. Seed Organization
        print("Seeding Organization...")
        Organization = Aras.Model._registry["Organization"]
        hq, created = Organization.get_or_create(
            db,
            {
                "name": "Headquarters",
                "legal_name": "Aras Framework HQ",
                "base_currency_id": idr.id,
                "address": "Jakarta, Indonesia",
                "phone": "+62 21 123456",
                "email": "hq@aras.io"
            },
            id=1, code="HQ"
        )
        db.commit()

        # 3. Seed CoA and Link to Company
        print("Seeding Chart of Accounts...")
        slugs = seed_coa(db, hq.id)
        
        # Link default accounts to company
        hq.acc_cash_default_id = slugs.get("cash").id if slugs.get("cash") else None
        hq.acc_bank_default_id = slugs.get("bank").id if slugs.get("bank") else None
        hq.acc_receivable_default_id = slugs.get("receivable").id if slugs.get("receivable") else None
        hq.acc_payable_default_id = slugs.get("payable").id if slugs.get("payable") else None
        hq.acc_income_default_id = slugs.get("revenue").id if slugs.get("revenue") else None
        hq.acc_cogs_default_id = slugs.get("cogs").id if slugs.get("cogs") else None
        hq.acc_inventory_default_id = slugs.get("inventory").id if slugs.get("inventory") else None
        hq.acc_tax_output_ppn_id = slugs.get("tax_output").id if slugs.get("tax_output") else None
        db.add(hq)
        db.commit()

        # 4. Seed UOMs
        print("Seeding Units of Measure...")
        Uom = Aras.Model._registry["Uom"]
        uoms = [
            ("Unit", "Unit"),
            ("Box", "Box"),
            ("Kg", "Kilogram"),
            ("Ltr", "Liter"),
            ("Mtr", "Meter"),
            ("Pcs", "Pieces"),
        ]
        for code, name in uoms:
            Uom.get_or_create(db, {"name": name}, code=code)
        db.commit()

        # 5. Seed Price Types
        print("Seeding Price Types...")
        PriceType = Aras.Model._registry["PriceType"]
        price_types = [
            ("Standard Sales", "SLS-STD", "sales"),
            ("Standard Purchase", "PUR-STD", "purchase"),
            ("Wholesale", "SLS-WHL", "sales"),
            ("Promotion", "SLS-PRM", "sales"),
        ]
        for name, code, kind in price_types:
            PriceType.get_or_create(db, {"kind": kind, "name": name}, code=code)
        db.commit()

        # 6. Seed Locations
        print("Seeding Locations...")
        Location = Aras.Model._registry["Location"]
        Location.get_or_create(db, {"name": "Main Warehouse", "location_type": "Internal"}, org_id=hq.id, code="WH-MAIN")
        Location.get_or_create(db, {"name": "Transit Location", "location_type": "Transit"}, org_id=hq.id, code="LOC-TRANSIT")
        db.commit()

        # 7. Seed Product Categories
        print("Seeding Product Categories...")
        ProductCategory = Aras.Model._registry["ProductCategory"]
        pc_gen, _ = ProductCategory.get_or_create(
            db, 
            {
                "name": "General",
                "account_stock_id": hq.acc_inventory_default_id,
                "account_cogs_id": hq.acc_cogs_default_id,
            }, 
            org_id=hq.id, code="CAT-GEN"
        )
        db.commit()

        # 8. Seed Payment Modes
        print("Seeding Payment Modes...")
        ModeOfPayment = Aras.Model._registry["ModeOfPayment"]
        CompanyPaymentAccount = Aras.Model._registry["OrganizationPaymentAccount"]
        
        cash_mode, _ = ModeOfPayment.get_or_create(db, {"name": "Cash", "payment_type": "Cash"}, org_id=hq.id, code="PAY-CASH")
        bank_mode, _ = ModeOfPayment.get_or_create(db, {"name": "Bank Transfer", "payment_type": "Bank"}, org_id=hq.id, code="PAY-BANK")
        
        # Add accounts to payment modes if not already there
        if not cash_mode.accounts and hq.acc_cash_default_id:
            CompanyPaymentAccount.create(db, {"mode_id": cash_mode.id, "account_id": hq.acc_cash_default_id})
        if not bank_mode.accounts and hq.acc_bank_default_id:
            CompanyPaymentAccount.create(db, {"mode_id": bank_mode.id, "account_id": hq.acc_bank_default_id})
        
        db.commit()

        print("Basic data seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed_basic_data()
