import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re
import json

BASE = "http://127.0.0.1:8080"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# 1. Get Login Page to get CSRF
res = opener.open(f"{BASE}/auth/login")
html = res.read().decode("utf-8")
m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
if not m:
    m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
csrf = m.group(1) if m else None

# 2. POST Login
data = urllib.parse.urlencode({
    "csrf_token": csrf,
    "email_or_username": "admin@example.com",
    "password": "admin123",
    "remember_me": "y",
}).encode()
req = urllib.request.Request(f"{BASE}/auth/login", data=data, method="POST")
req.add_header("Content-Type", "application/x-www-form-urlencoded")
req.add_header("Referer", f"{BASE}/auth/login")
res = opener.open(req)
print("Login redirect final URL:", res.url)

# 3. Fetch UI Init
try:
    req2 = urllib.request.Request(f"{BASE}/admin/api/ui/init")
    res2 = opener.open(req2)
    print("UI Init Status:", res2.status)
    content = res2.read().decode("utf-8")
    try:
        data = json.loads(content)
        print("UI Init JSON loaded successfully. Menu items:", len(data.get("menu", [])))
    except json.JSONDecodeError:
        print("UI Init returned invalid JSON:")
        print(content[:500])
except urllib.error.HTTPError as e:
    print(f"UI Init ERROR {e.code}: {e.reason}")
    print(e.read().decode("utf-8")[:500])
