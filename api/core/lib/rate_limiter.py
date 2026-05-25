"""
Purpose: Simple in-memory rate limiter middleware for FastAPI.
Context: Added to main.py as a Starlette middleware.
Impact: Protects all endpoints from abuse via sliding window per IP.
"""
import time
from collections import defaultdict, deque
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.
    Defaults: 200 requests per 60s per IP. Auth endpoints: 10 per 60s.
    """
    _windows: dict = defaultdict(deque)

    # (max_requests, window_seconds)
    _ROUTE_LIMITS: dict = {
        "/api/v1/auth/token": (10, 60),
        "/api/v1/auth/register": (5, 60),
        "/api/v1/auth/forgot-password": (5, 300),
        "/api/v1/auth/reset-password": (5, 300),
    }
    _DEFAULT = (200, 60)

    async def dispatch(self, request: Request, call_next):
        ip = request.client.host if request.client else "unknown"
        path = request.url.path
        max_req, window = self._ROUTE_LIMITS.get(path, self._DEFAULT)
        key = f"{ip}:{path}"
        now = time.monotonic()

        dq = self._windows[key]
        # Evict old entries outside window
        while dq and dq[0] < now - window:
            dq.popleft()

        if len(dq) >= max_req:
            retry_after = int(window - (now - dq[0])) + 1
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"status": "error", "message": "Rate limit exceeded. Try again later.", "code": 429},
                headers={"Retry-After": str(retry_after)},
            )

        dq.append(now)
        return await call_next(request)
