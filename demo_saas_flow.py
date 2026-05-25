import requests
import time
import json
import subprocess

# URLs for Control Panel and Tenant
CP_URL = "http://localhost:8000/api/v1"
TENANT_URL = "http://localhost:8001/api/v1"

def print_step(msg):
    print(f"\n--- {msg} ---")

def demo():
    # 1. Signup
    print_step("1. User Signup")
    signup_data = {
        "email": f"demo_customer_{int(time.time())}@example.com",
        "company_name": "Demo Corp",
        "full_name": "Demo User",
        "plan_id": 4  # Business Plan
    }
    resp = requests.post(f"{CP_URL}/saas/signup", json=signup_data)
    print(f"Signup response: {resp.status_code} - {resp.json()}")
    sub_id = resp.json().get("subscription_id")

    # 2. Approve (Simulate Admin Action via local script execution in Docker)
    print_step("2. Admin Approving Subscription")
    # We'll use docker exec to run a model action 'approve' on the Subscription object
    approve_cmd = f"docker exec aras-control-panel-1 python -c \"import json; from core import Aras; from apps.saas.models import Subscription; db=next(Aras.get_db()); sub=db.get(Subscription, {sub_id}); res=sub.approve(db); db.commit(); print(json.dumps(res))\""
    approve_output = subprocess.check_output(approve_cmd, shell=True).decode()
    approve_res = json.loads(approve_output.strip())
    print(f"Full Approve Response: {json.dumps(approve_res, indent=2)}")
    print(f"Approve Result: {approve_res['message']}")
    license_token = approve_res['data']['license_token']
    print(f"Issued License Token: {license_token[:50]}...")

    # 3. Tenant fetches Config
    print_step("3. Tenant Fetching Config from Control Panel")
    headers = {"Authorization": f"Bearer {license_token}"}
    resp = requests.get(f"{CP_URL}/saas/tenant-config", headers=headers)
    print(f"Tenant Config (Modules): {resp.json().get('active_modules')}")
    
    # 4. Control: Update Plan to Lite (ID 2)
    print_step("4. Control: Downgrading Plan to Lite")
    update_cmd = f"docker exec aras-control-panel-1 python -c \"from core import Aras; from apps.saas.models import Subscription; db=next(Aras.get_db()); sub=db.get(Subscription, {sub_id}); sub.plan_id=2; db.commit(); print('Success')\""
    subprocess.check_call(update_cmd, shell=True)
    
    # Fetch config again
    resp = requests.get(f"{CP_URL}/saas/tenant-config", headers=headers)
    print(f"Updated Tenant Config (Plan: {resp.json().get('plan_key')}): {resp.json().get('active_modules')}")

    # 5. Control: Suspend Subscription
    print_step("5. Control: Suspending Subscription")
    suspend_cmd = f"docker exec aras-control-panel-1 python -c \"from core import Aras; from apps.saas.models import Subscription; db=next(Aras.get_db()); sub=db.get(Subscription, {sub_id}); sub.suspend(db); db.commit(); print('Success')\""
    subprocess.check_call(suspend_cmd, shell=True)
    
    # Fetch config again - should fail
    resp = requests.get(f"{CP_URL}/saas/tenant-config", headers=headers)
    print(f"Tenant Config after Suspension: {resp.status_code} - {resp.json()}")

if __name__ == "__main__":
    demo()
