import urllib.request
import urllib.parse
import json

base_url = "http://localhost:8000/api/v1"

def req(url, data=None, method="POST", token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    encoded_data = None
    if data is not None:
        if isinstance(data, dict) and "username" in data:
            # form urlencoded
            encoded_data = urllib.parse.urlencode(data).encode('utf-8')
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            # json
            encoded_data = json.dumps(data).encode('utf-8')
            headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

# 1. Login
status, resp = req(f"{base_url}/auth/token", data={"username": "admin", "password": "password"})
if status != 200:
    status, resp = req(f"{base_url}/auth/token", data={"username": "admin", "password": "admin"})
    
print("LOGIN:", status)
token = resp.get("access_token")

# 2. Sync
status1, resp1 = req(f"{base_url}/dev/sync", method="POST", token=token, data={})
print("SYNC:", status1, resp1)

# 3. Query
status2, resp2 = req(f"{base_url}/query/sys_settings", data={"filters": []}, token=token)
print("QUERY:", status2, resp2)
