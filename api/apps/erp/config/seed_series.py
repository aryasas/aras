"""
Seed initial naming series for all ERP document types.
Series data lives in DB (aras_naming_series) — editable via ERP Settings UI.
Run: cd api && python apps/erp/config/seed_series.py
"""
import sys
sys.path.insert(0, ".")

from core.lib.database import SessionLocal
from core.registry.series import Series

SERIES = [
    {"key": "erp_accounting_sales_invoices", "prefix": "INV-", "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_accounting_sales_orders",   "prefix": "SO-",  "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_stock_movements",           "prefix": "MV-",  "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_accounting_entries",        "prefix": "JE-",  "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_stock_delivery_orders",     "prefix": "DO-",  "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_stock_receipts",            "prefix": "GR-",  "format": "{prefix}{year}-{next_value:04d}", "config": {"reset_yearly": True}},
    {"key": "erp_crm_customers",             "prefix": "CUS-", "format": "{prefix}{next_value:05d}",        "config": {}},
]


def run():
    db = SessionLocal()
    try:
        for s in SERIES:
            existing = db.query(Series).filter_by(key=s["key"]).first()
            if existing:
                print(f"[SKIP] {s['key']}")
                continue
            db.add(Series(
                key=s["key"],
                prefix=s["prefix"],
                format=s["format"],
                next_value=1,
                config=s["config"],
            ))
            print(f"[OK]   {s['key']} → {s['prefix']}")
        db.commit()
    finally:
        db.close()
    print("Done.")


if __name__ == "__main__":
    run()
