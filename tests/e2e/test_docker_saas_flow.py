# gemini-pro
import httpx
import pytest
import time
import os

BASE_URL = os.getenv("ARAS_CONTROL_PANEL_URL", "http://localhost:8000")
TENANT_URLS = {
    "tenant-1": "http://localhost:8001",
    "tenant-2": "http://localhost:8002",
    "tenant-3": "http://localhost:8003",
    "tenant-4": "http://localhost:8004",
}

def wait_for_ready(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = httpx.get(url, timeout=2)
            if r.status_code == 200:
                return
        except:
            pass
        time.sleep(2)
    raise TimeoutError(f"Timed out waiting for {url}")

@pytest.mark.docker_e2e
def test_saas_flow():
    if os.getenv("DOCKER_E2E") != "1":
        pytest.skip("DOCKER_E2E not set to 1")

    # 1. Wait for control panel readiness
    wait_for_ready(f"{BASE_URL}/api/v1/health")

    client = httpx.Client(timeout=30)

    # 2. Verify plans
    r = client.get(f"{BASE_URL}/api/v1/saas/plans/public")
    assert r.status_code == 200
    plans = r.json()
    assert len(plans) >= 4
    
    plan_map = {p["plan_key"]: p["id"] for p in plans}
    for key in ["free", "lite", "growth", "business"]:
        assert key in plan_map

    # 3. Register 4 demo accounts
    demos = [
        {"email": "demo-free@aras.test", "company": "tenant-1", "plan": "free"},
        {"email": "demo-lite@aras.test", "company": "tenant-2", "plan": "lite"},
        {"email": "demo-growth@aras.test", "company": "tenant-3", "plan": "growth"},
        {"email": "demo-business@aras.test", "company": "tenant-4", "plan": "business"},
    ]
    
    results = {}

    for demo in demos:
        print(f"Registering {demo['email']}...")
        r = client.post(f"{BASE_URL}/api/v1/saas/portal/register", json={
            "email": demo["email"],
            "password": "Demo1234!",
            "company_name": demo["company"],
            "full_name": f"Demo {demo['plan'].capitalize()}",
            "plan_id": plan_map[demo["plan"]]
        })
        if r.status_code == 409:
            # Re-login to get token if already exists
            r = client.post(f"{BASE_URL}/api/v1/saas/portal/login", json={
                "email": demo["email"],
                "password": "Demo1234!"
            })
            assert r.status_code == 200
            data = r.json()
        else:
            assert r.status_code == 200
            data = r.json()
            
        results[demo["plan"]] = {
            "email": demo["email"],
            "tenant_id": data["tenant_id"],
            "token": data["token"]
        }

    # 4. Activate via dev-bypass
    for plan, res in results.items():
        print(f"Activating {plan} via dev-bypass...")
        r = client.post(
            f"{BASE_URL}/api/v1/saas/portal/payment/dev-bypass", 
            json={"provider": "dev"},
            headers={"Authorization": f"Bearer {res['token']}"}
        )
        assert r.status_code == 200
        res["license_token"] = r.json()["license_token"]

    # 5. Provision tenant DB (Manual call)
    r = client.post(f"{BASE_URL}/api/v1/auth/token", data={
        "username": "admin",
        "password": "admin"
    })
    assert r.status_code == 200
    cp_admin_token = r.json()["access_token"]
    cp_headers = {"Authorization": f"Bearer {cp_admin_token}"}

    for plan, res in results.items():
        tenant_id = res["tenant_id"]
        print(f"Provisioning {tenant_id}...")
        r = client.post(f"{BASE_URL}/api/v1/saas/control-panel/tenants/provision", 
                        json={"tenant_id": tenant_id},
                        headers=cp_headers)
        # 400 if already provisioned
        assert r.status_code in (200, 201, 400)
        
        print(f"Seeding {tenant_id}...")
        r = client.post(f"{BASE_URL}/api/v1/saas/control-panel/tenants/{tenant_id}/seed", 
                        headers=cp_headers)
        assert r.status_code in (200, 404)

    # 6. Operational checks per tenant
    plan_to_tenant = {
        "free": "tenant-1",
        "lite": "tenant-2",
        "growth": "tenant-3",
        "business": "tenant-4",
    }

    for plan, container in plan_to_tenant.items():
        res = results[plan]
        t_url = TENANT_URLS[container]
        wait_for_ready(f"{t_url}/api/v1/health")
        
        print(f"Checking tenant {container} ({plan})...")
        r = client.post(f"{t_url}/api/v1/auth/token", data={
            "username": "admin",
            "password": "admin"
        })
        assert r.status_code == 200
        t_token = r.json()["access_token"]
        t_headers = {"Authorization": f"Bearer {t_token}"}
        
        # Smoke tests
        if plan == "free":
            r = client.get(f"{t_url}/api/v1/accounting/accounts", headers=t_headers)
            assert r.status_code == 200
        elif plan == "lite":
            r = client.post(f"{t_url}/api/v1/accounting/entries", json={
                "doc_date": "2026-05-30",
                "narrative": "E2E Test Entry",
                "currency_id": 1 # Assumed base currency
            }, headers=t_headers)
            assert r.status_code == 201
        elif plan == "growth":
            r = client.get(f"{t_url}/api/v1/report/reports", headers=t_headers)
            assert r.status_code == 200
        elif plan == "business":
            r = client.get(f"{t_url}/api/v1/saas/tenant-config", headers={"Authorization": f"Bearer {res['license_token']}"})
            assert r.status_code == 200
            assert r.json()["api_access"] is True

    # 7. Control reachability
    for plan, res in results.items():
        tenant_id = res["tenant_id"]
        print(f"Pinging {tenant_id} from CP...")
        r = client.post(f"{BASE_URL}/api/v1/saas/control-panel/tenants/{tenant_id}/ping", headers=cp_headers)
        assert r.status_code == 200
        assert r.json()["reachable"] is True

    print("\nE2E Test Passed for all 4 plans!")
