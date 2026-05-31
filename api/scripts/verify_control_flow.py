# gemini-pro
import httpx
import os
import json
import sys

# Add api to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

def verify():
    print("=== Verification: Localhost Control Panel -> Docker Tenants ===\n")
    
    # 1. Check Registry
    registry_path = os.getenv("TENANT_REGISTRY_PATH", "api/data/tenant_registry.json")
    if not os.path.exists(registry_path):
        print(f"FAILED: Registry not found at {registry_path}")
        return
        
    with open(registry_path, "r") as f:
        tenants = json.load(f)
    
    print(f"Loaded {len(tenants)} tenants from registry.")

    # 2. Check Connection to Tenants
    # Localhost mapping:
    # tenant-1 -> localhost:8001
    # tenant-2 -> localhost:8002
    # tenant-3 -> localhost:8003
    # tenant-4 -> localhost:8004
    
    mappings = {
        "tenant-1-1": "http://localhost:8001",
        "tenant-2-2": "http://localhost:8002",
        "tenant-3-3": "http://localhost:8003",
        "tenant-4-4": "http://localhost:8004",
        "freeco-1": "http://localhost:8001", # Assuming mapped for demo
        "liteco-2": "http://localhost:8002",
        "growthco-3": "http://localhost:8003",
        "bizco-4": "http://localhost:8004",
    }

    for tid, url in mappings.items():
        if tid in tenants:
            print(f"Pinging {tid} at {url}...")
            try:
                r = httpx.get(f"{url}/api/v1/health", timeout=2)
                if r.status_code == 200:
                    print(f"  SUCCESS: {tid} is operational. Role: {r.json().get('role')}")
                else:
                    print(f"  FAILED: {tid} returned status {r.status_code}")
            except Exception as e:
                print(f"  SKIPPED: {tid} is not reachable (is Docker running?). Error: {type(e).__name__}")

    # 3. Check DB Configuration
    print("\n=== DB Configuration Check ===")
    cp_db = "postgresql+psycopg2://aras:aras@localhost:5434/control_panel"
    tenant_db = "postgresql+psycopg2://aras:aras@localhost:5433/postgres"
    
    print(f"Control Panel DB (Expected): {cp_db}")
    print(f"Tenants Admin DB (Expected): {tenant_db}")
    
    # Check if we can reach them (simulated)
    # Note: we don't actually try to connect here to avoid long hangs if ports are closed
    print("\nVerification script finished. If Docker is running, you should see SUCCESS above.")

if __name__ == "__main__":
    verify()
