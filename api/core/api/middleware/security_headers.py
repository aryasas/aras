from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.lib.settings import settings

_spa_origins = tuple(origin for origin in settings.CORS_ORIGINS if origin)
_source_list = " ".join(dict.fromkeys(("'self'", *_spa_origins)))

# gpt-5
CSP_POLICY = "; ".join(
    [
        f"default-src {_source_list}",
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        f"connect-src {_source_list}",
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net",
        "img-src 'self' data:",
        "font-src 'self' data: https://cdn.jsdelivr.net",
        "object-src 'none'",
        "base-uri 'self'",
        "frame-ancestors 'none'",
    ]
)


# gpt-5
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    # gpt-5
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = CSP_POLICY
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response
