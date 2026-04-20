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

    def post_multipart(self, path: str, fields: dict, files: dict = None) -> Tuple[int, str, str]:
        """POST multipart/form-data with optional file uploads.
        files: {field_name: (filename, bytes, content_type)}
        """
        import uuid
        boundary = uuid.uuid4().hex
        body_parts = []

        for name, value in (fields or {}).items():
            body_parts.append(
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'
                f'{value}\r\n'
            )

        for field_name, (filename, data, content_type) in (files or {}).items():
            header = (
                f'--{boundary}\r\n'
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
                f'Content-Type: {content_type}\r\n\r\n'
            )
            body_parts.append(header.encode() + (data if isinstance(data, bytes) else data.encode()) + b'\r\n')

        encoded = b""
        for part in body_parts:
            encoded += part if isinstance(part, bytes) else part.encode()
        encoded += f'--{boundary}--\r\n'.encode()

        req = urllib.request.Request(
            self.base + path,
            data=encoded,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
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
        """Extract CSRF token from HTML (last response by default).
        Handles both name="csrf_token" and name="_csrf_token" variants.
        """
        src = html or self.last_html
        # Try csrf_token first, then _csrf_token
        for name in ("csrf_token", "_csrf_token"):
            m = re.search(rf'name="{name}"[^>]*value="([^"]+)"', src)
            if not m:
                m = re.search(rf'value="([^"]+)"[^>]*name="{name}"', src)
            if m:
                return m.group(1)
        return None

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
