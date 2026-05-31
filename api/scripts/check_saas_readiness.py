# gemini-pro
import sys
import os

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core import Aras
from core.lib.database import SessionLocal
from core.tenant.registry import tenant_registry
import logging

logging.basicConfig(level=logging.INFO)

def check_readiness():
    Aras.logic.discovery.discover_apps(package_path="apps")
    db = SessionLocal()
    
    print("\n=== SaaS Readiness Report ===")
    
    # 1. Check Plans
    from apps.saas.models import Plan
    try:
        plans = db.query(Plan).all()
        print(f"Plans found: {len(plans)}")
        for p in plans:
            print(f" - [{p.plan_key}] {p.name}: {p.price} {p.currency} (Active: {p.is_active})")
    except Exception as e:
        print(f"Error checking plans: {e}")

    # 2. Check Subscriptions
    from apps.saas.models import Subscription
    try:
        subs = db.query(Subscription).all()
        print(f"\nSubscriptions found: {len(subs)}")
        for s in subs:
            print(f" - {s.company_name} ({s.email}) -> Tenant: {s.tenant_id}, Status: {s.status}")
    except Exception as e:
        print(f"Error checking subscriptions: {e}")

    # 3. Check Tenant Registry
    print("\n=== Tenant Registry (data/tenant_registry.json) ===")
    tenants = tenant_registry.list_all()
    print(f"Tenants in registry: {len(tenants)}")
    for t in tenants:
        print(f" - ID: {t['tenant_id']}, DB: {t['db_url']}")

    # 4. Check Roles
    print("\n=== Environment Roles ===")
    print(f"ARAS_ROLE: {os.getenv('ARAS_ROLE', 'not set')}")
    print(f"ARAS_MODE: {os.getenv('ARAS_MODE', 'not set')}")

    db.close()

if __name__ == "__main__":
    check_readiness()
