import requests
import json

session = requests.Session()
res = session.post("http://127.0.0.1:8080/admin/auth/login", data={"email": "admin@aras.com", "password": "1"})
if "Dashboard" not in res.text and "aras" not in res.text:
    print("Login failed?")

res = session.get("http://127.0.0.1:8080/admin/erp/configuration/")
print(res.status_code)
with open("out.html", "w") as f:
    f.write(res.text)
