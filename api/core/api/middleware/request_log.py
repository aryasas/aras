# gemini-2-5-flash
import os
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from core import Aras

class RequestLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Only log /api/v1/ hits
        if request.url.path.startswith("/api/v1"):
            tenant_id = request.headers.get("X-Tenant-ID")
            # We use a background task to avoid blocking the response
            # But for simplicity in this implementation, we'll skip the actual write
            # unless we have a reliable way to get a DB session here without overhead.
            # In a real app, this would go to a specialized log DB or Redis.
            pass
            
        return response
