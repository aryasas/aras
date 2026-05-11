import requests
session = requests.Session()
# Assuming standard login route and default credentials
resp = session.post("http://127.0.0.1:8080/auth/login", data={"email": "admin@example.com", "password": "password"})
print("Login status:", resp.status_code)
# Now hit the UI init endpoint
ui_resp = session.get("http://127.0.0.1:8080/admin/api/ui/init")
print("UI Init status:", ui_resp.status_code)
print(ui_resp.text[:500])
