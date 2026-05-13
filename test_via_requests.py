import requests
import json

base_url = "http://localhost:8000/api/v1"

# 1. Login
try:
    resp = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "password"})
    if resp.status_code != 200:
        resp = requests.post(f"{base_url}/auth/login", data={"username": "admin", "password": "admin"})
    
    print("LOGIN:", resp.status_code)
    token = resp.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Sync
    resp1 = requests.post(f"{base_url}/dev/sync", headers=headers)
    print("SYNC:", resp1.status_code, resp1.text)

    # 3. Query settings
    resp2 = requests.post(f"{base_url}/query/sys_settings", json={"filters": []}, headers=headers)
    print("QUERY:", resp2.status_code, resp2.text)

except Exception as e:
    print("ERROR:", e)

