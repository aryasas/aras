import hashlib
import os
import secrets
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.lib.settings import settings

_spa_origins = tuple(origin for origin in settings.CORS_ORIGINS if origin)
_source_list = " ".join(dict.fromkeys(("'self'", *_spa_origins)))

# gemini-3-flash-preview
def _get_ui_inline_script_hash():
    """Reads ui/index.html and computes the sha256 hash of the first inline script."""
    ui_index = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "ui", "index.html")
    if not os.path.exists(ui_index):
        return None
    try:
        with open(ui_index, "r") as f:
            content = f.read()
        import re
        # Extract content between <script> and </script> - the first one found
        match = re.search(r"<script>(.*?)</script>", content, re.DOTALL)
        if match:
            script_content = match.group(1)
            sha256 = hashlib.sha256(script_content.encode("utf-8")).digest()
            import base64
            return f"'sha256-{base64.b64encode(sha256).decode('utf-8')}'"
    except Exception:
        pass
    return None

_ui_script_hash = _get_ui_inline_script_hash()

# gemini-3-flash-preview
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    # gemini-3-flash-preview
    async def dispatch(self, request: Request, call_next):
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce

        # script-src 'self' 'nonce-<value>' https://cdn.jsdelivr.net
        # style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net
        # TODO: Tailwind utility classes inject inline styles pervasively; 
        # nonce-ing every style is not feasible yet. Added style-src-attr 'unsafe-inline' 
        # to at least scope it explicitly to attributes where needed.
        
        script_src = f"script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net"
        if _ui_script_hash:
            script_src += f" {_ui_script_hash}"
            
        csp_policy = "; ".join(
            [
                f"default-src {_source_list}",
                script_src,
                f"connect-src {_source_list}",
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
                "style-src-attr 'unsafe-inline'", # gemini-3-flash-preview: scoping style attributes
                "img-src 'self' data:",
                "font-src 'self' data: https://cdn.jsdelivr.net",
                "object-src 'none'",
                "base-uri 'self'",
                "frame-ancestors 'none'",
                "report-uri /api/v1/csp-report", # gemini-3-flash-preview: violation reporting
                "report-to default", # gemini-3-flash-preview: modern violation reporting
            ]
        )

        response = await call_next(request)
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["Reporting-Endpoints"] = 'default="/api/v1/csp-report"'
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=(), payment=()"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
