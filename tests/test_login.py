#!/usr/bin/env python3
"""
test_login.py — CLI test login end-to-end via HTTP
Usage: python test_login.py
"""
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re

BASE = "http://localhost:8080"

def get_csrf_token(html):
    m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    if not m:
        m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', html)
    return m.group(1) if m else None

def test_login(email, password):
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    # Step 1: GET login page
    try:
        res = opener.open(f"{BASE}/auth/login")
        html = res.read().decode("utf-8")
        print(f"[1] GET /auth/login → {res.status} {res.url}")
    except urllib.error.HTTPError as e:
        print(f"[1] GET /auth/login → ERROR {e.code}: {e.reason}")
        return False

    csrf = get_csrf_token(html)
    print(f"[2] CSRF token: {csrf[:20]}..." if csrf else "[2] CSRF token: NOT FOUND")

    if not csrf:
        print("    ⚠ Kemungkinan form tidak ada atau halaman error")
        print("    --- HTML snippet ---")
        print(html[:800])
        return False

    # Step 2: POST login
    data = urllib.parse.urlencode({
        "csrf_token": csrf,
        "email_or_username": email,
        "password": password,
        "remember_me": "y",
    }).encode()

    req = urllib.request.Request(f"{BASE}/auth/login", data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Referer", f"{BASE}/auth/login")

    try:
        res = opener.open(req)
        final_url = res.url
        status = res.status
        html2 = res.read().decode("utf-8")
        print(f"[3] POST /auth/login → {status} redirect → {final_url}")
    except urllib.error.HTTPError as e:
        print(f"[3] POST /auth/login → ERROR {e.code}: {e.reason}")
        body = e.read().decode("utf-8")
        print("    --- Flash/Error snippet ---")
        # cari flash message
        for line in body.splitlines():
            if any(k in line.lower() for k in ["alert", "flash", "error", "invalid", "danger"]):
                print("   ", line.strip())
        return False

    # Step 3: Cek apakah berhasil redirect ke dashboard
    if "dashboard" in final_url or "admin" in final_url:
        print(f"[✅] LOGIN BERHASIL → {final_url}")
        return True
    else:
        print(f"[❌] LOGIN GAGAL → masih di {final_url}")
        # Cari flash message di html2
        for line in html2.splitlines():
            if any(k in line.lower() for k in ["alert", "flash", "error", "invalid", "danger"]):
                print("   ", line.strip())
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Test login: admin@example.com / admin123")
    print("=" * 50)
    ok = test_login("admin@example.com", "admin123")
    print("=" * 50)
    if not ok:
        print("\nTest dengan username...")
        print("=" * 50)
        test_login("admin", "admin123")
