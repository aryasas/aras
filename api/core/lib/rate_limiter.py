"""
Purpose: Sliding-window rate limiter middleware for FastAPI.
Context: Added to main.py as a Starlette middleware.
Impact: Protects all endpoints from abuse. Uses Redis when available; falls back to in-memory.
"""
import time
import logging
import os
from collections import defaultdict, deque
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

def _make_redis_client():
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis
        client = redis.from_url(url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return client
    except Exception as e:
        logger.warning(f"[RateLimiter] Redis unavailable ({e}), falling back to in-memory")
        return None

_redis = _make_redis_client()

# claude-sonnet-4-6
class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Sliding-window rate limiter.
    Defaults: 200 requests per 60s per IP. Auth endpoints: 10 per 60s.
    Key: user_id post-auth, IP otherwise.
    Uses Redis backend when REDIS_URL is set; gracefully falls back to in-memory.
    """
    _windows: dict = defaultdict(deque)

    _ROUTE_LIMITS: dict = {
        "/api/v1/auth/token": (10, 60),
        "/api/v1/auth/register": (5, 60),
        "/api/v1/auth/forgot-password": (5, 300),
        "/api/v1/auth/reset-password": (5, 300),
    }
    _DEFAULT = (200, 60)

    def _get_key(self, request: Request, path: str) -> str:
        user = getattr(getattr(request, "state", None), "user", None)
        if user is not None:
            uid = getattr(user, "id", None) or getattr(user, "user_id", None)
            if uid:
                return f"uid:{uid}:{path}"
        ip = request.client.host if request.client else "unknown"
        return f"ip:{ip}:{path}"

    def _check_redis(self, key: str, max_req: int, window: int) -> tuple[bool, int]:
        """Returns (allowed, retry_after). Uses Redis sorted set sliding window."""
        try:
            now = time.time()
            pipe = _redis.pipeline()
            pipe.zremrangebyscore(key, 0, now - window)
            pipe.zcard(key)
            pipe.zadd(key, {str(now): now})
            pipe.expire(key, window + 1)
            results = pipe.execute()
            count = results[1]
            if count >= max_req:
                oldest = _redis.zrange(key, 0, 0, withscores=True)
                retry_after = int(window - (now - oldest[0][1])) + 1 if oldest else window
                return False, retry_after
            return True, 0
        except Exception as e:
            logger.warning(f"[RateLimiter] Redis error ({e}), falling back to in-memory for this request")
            return None, 0  # type: ignore

    def _check_memory(self, key: str, max_req: int, window: int) -> tuple[bool, int]:
        now = time.monotonic()
        dq = self._windows[key]
        while dq and dq[0] < now - window:
            dq.popleft()
        if len(dq) >= max_req:
            retry_after = int(window - (now - dq[0])) + 1
            return False, retry_after
        dq.append(now)
        return True, 0

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        max_req, window = self._ROUTE_LIMITS.get(path, self._DEFAULT)
        key = self._get_key(request, path)

        if _redis is not None:
            allowed, retry_after = self._check_redis(key, max_req, window)
            if allowed is None:
                allowed, retry_after = self._check_memory(key, max_req, window)
        else:
            allowed, retry_after = self._check_memory(key, max_req, window)

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"status": "error", "message": "Rate limit exceeded. Try again later.", "code": 429},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
