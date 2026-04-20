# -*- coding: utf-8 -*-
"""
test/client.py — Shared HTTP session client for all web tests.
Handles cookies, CSRF extraction, and response helpers.
"""
import re
import http.cookiejar
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Tuple


class Client:
    """Stateful HTTP client with cookie + CSRF support."""

    def __init__(self, base_url: str):
        self.base = base_url.rstrip("/")
        self._jar = http.cookiejar.CookieJar()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self._jar),
            urllib.request.HTTPRedirectHandler(),
        )
        self.last_status: int = 0
        self.last_url: str = ""
        self.last_html: str = ""

    # ── low-level ──────────────────────────────────────────────────────────

    def get(self, path: str) -> Tuple[int, str, str]:
        """GET request. Returns (status, final_url, html)."""
        try:
            res = self._opener.open(self.base + path)
            html = res.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = res.status, res.url, html
            return res.status, res.url, html
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = e.code, e.url, body
            return e.code, e.url, body

    def post(self, path: str, data: dict, json: bool = False) -> Tuple[int, str, str]:
        """POST request with form data. Returns (status, final_url, html)."""
        encoded = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(
            self.base + path,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        try:
            res = self._opener.open(req)
            html = res.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = res.status, res.url, html
            return res.status, res.url, html
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = e.code, e.url, body
            return e.code, e.url, body

    def post_json(self, path: str, payload: dict) -> Tuple[int, str, str]:
        """POST JSON body. Returns (status, final_url, body_str)."""
        import json
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.base + path,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        try:
            res = self._opener.open(req)
            body = res.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = res.status, res.url, body
            return res.status, res.url, body
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            self.last_status, self.last_url, self.last_html = e.code, e.url, body
            return e.code, e.url, body

    def request_json(self, method: str, path: str, payload: dict = None) -> Tuple[int, str]:
        """Generic JSON request (GET/POST/PUT/DELETE). Returns (status, body_str)."""
        import json
        data = json.dumps(payload or {}).encode() if method in ("POST", "PUT") else None
        req = urllib.request.Request(
            self.base + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            res = self._opener.open(req)
            body = res.read().decode("utf-8", errors="replace")
            return res.status, body
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            return e.code, body

    # ── helpers ────────────────────────────────────────────────────────────

    def csrf(self, html: str = None) -> Optional[str]:
        """Extract CSRF token from HTML (last response by default)."""
        src = html or self.last_html
        m = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', src)
        if not m:
            m = re.search(r'value="([^"]+)"[^>]*name="csrf_token"', src)
        return m.group(1) if m else None

    def login(self, username: str, password: str) -> bool:
        """Login flow: GET /auth/login → POST with CSRF. Returns True on success."""
        _, _, html = self.get("/auth/login")
        token = self.csrf(html)
        if not token:
            return False
        status, url, _ = self.post("/auth/login", {
            "csrf_token": token,
            "email_or_username": username,
            "password": password,
        })
        return "/admin" in url or "dashboard" in url

    def logout(self):
        self.get("/auth/logout")

    def is_on(self, *keywords: str) -> bool:
        """Check if any keyword appears in last response URL or HTML."""
        combined = self.last_url + self.last_html
        return any(k in combined for k in keywords)

    def contains(self, text: str) -> bool:
        return text in self.last_html
