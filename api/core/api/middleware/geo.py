# gemini-2-5-flash
import os
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from ...lib.geo import country_from_ip

class GeoMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if os.getenv("ARAS_GEO_ROUTING") == "0":
            # Bypass geo routing
            request.state.geo_country = "US"
        else:
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                ip = forwarded.split(",")[0].strip()
                request.state.geo_country = country_from_ip(ip)
            else:
                request.state.geo_country = None
                
        response = await call_next(request)
        return response
