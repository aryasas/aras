import logging
import os
from pythonjsonlogger.json import JsonFormatter

from fastapi import FastAPI, Depends, HTTPException, Request, APIRouter
from typing import Any
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from core.lib.settings import settings
settings.validate()

from core import Aras

# --- Logging Configuration ---
def setup_logging():
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    root = logging.getLogger()
    root.setLevel(log_level)
    
    handler = logging.StreamHandler()
    formatter = JsonFormatter(
        '%(levelname)s %(asctime)s %(filename)s %(lineno)d %(process)d %(thread)d %(name)s %(message)s'
    )
    handler.setFormatter(formatter)
    root.addHandler(handler)
    
    # Suppress verbose loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

# Discover and load all apps
Aras.logic.discovery.discover_apps(package_path="apps")

# Register core master data entities
from core.registry.master_data_entities import register_core_entities
register_core_entities()

logger.info("Startup schema mutation disabled. Run Alembic migrations before starting the API.")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.manager.bootstrap import run as bootstrap
    from core.manager.service_bootstrap import register_services
    register_services()
    db = next(Aras.get_db())
    Aras.Manager.Audit.register_listeners()
    if settings.DEBUG or settings.TESTING:
        Aras.Manager.Sync.sync_all(db)
        bootstrap(db)
    else:
        logger.info("Production startup registry/bootstrap writes disabled. Run migrations and sync explicitly.")
    
    # SaaS Cron
    try:
        from apps.saas.cron import setup_cron
        setup_cron()
    except Exception as e:
        logger.warning(f"Failed to setup SaaS cron: {e}")
        
    yield

app = FastAPI(
    title="Aras API",
    description="Metadata-driven Application Framework powered by FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Exception Handlers
from fastapi.exceptions import RequestValidationError
from fastapi import status
from core.exceptions import ArasException
from core.response import err as aras_err

@app.exception_handler(ArasException)
async def aras_exception_handler(request: Request, exc: ArasException):
    return JSONResponse(status_code=exc.status, content=aras_err(exc.message, exc.detail))

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP Exception: %s",
        exc.detail,
        extra={"status_code": exc.status_code, "path": request.url.path},
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "message": exc.detail,
            "error": exc.detail,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    error_messages = [f"{err['msg']} ({'.'.join(map(str, err['loc']))})" for err in exc.errors()]
    log_message = "Request validation failed: " + "; ".join(error_messages)
    logger.warning(log_message, extra={"path": request.url.path, "errors": exc.errors()})

    # Combine error messages for the response
    error_detail = ". ".join(error_messages)
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "data": None,
            "message": "Input validation failed.",
            "error": error_detail,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled Exception: %s", exc, extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "message": "An unexpected internal server error occurred.",
            "error": str(exc) if settings.DEBUG else "An internal error occurred.",
        },
    )

@app.middleware("http")
async def license_check_middleware(request: Request, call_next):
    if os.getenv("ARAS_LICENSE_ENFORCE", "false").lower() == "true":
        path = request.url.path
        if not path.startswith(("/api/v1/auth/token", "/api/v1/health", "/api/v1/license", "/docs", "/openapi.json")):
            from core.auth.middleware import get_license_payload
            try:
                get_license_payload()
            except HTTPException as e:
                return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
    return await call_next(request)

# Geo Middleware
from core.api.middleware.geo import GeoMiddleware
app.add_middleware(GeoMiddleware)

# gemini-pro
@app.get("/api/v1/health")
def health():
    return {"ok": True, "role": os.getenv("ARAS_ROLE", "tenant")}

# discover_apps must be called after all core routes are defined or handled by RouterFactory
# Aras.logic.discovery.discover_apps(package_path="apps") is already called above.
from core.lib.rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# CORS — allow_origins=["*"] + allow_credentials=True violates the spec and is rejected by browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Org-ID", "X-Scope-Org-ID", "X-Tenant-ID"],
)

# Core Routes
from core.auth.routes import router as auth_router
from core.auth.service import get_current_user
app.include_router(auth_router, prefix="/api/v1")

# Tier 2 API Routers
app.include_router(Aras.api.query.router, prefix="/api/v1")
app.include_router(Aras.api.workflow.router, prefix="/api/v1")
app.include_router(Aras.api.admin.router, prefix="/api/v1/admin")
app.include_router(Aras.api.settings.router, prefix="/api/v1")
app.include_router(Aras.api.master_data.router, prefix="/api/v1")
app.include_router(Aras.api.dev.router, prefix="/api/v1/dev")
app.include_router(Aras.api.registry.router, prefix="/api/v1")
app.include_router(Aras.api.files.router, prefix="/api/v1")
app.include_router(Aras.api.dashboard.router, prefix="/api/v1")

# Tenant management & Control Panel
import os
aras_role = os.getenv("ARAS_ROLE", "tenant")

if aras_role == "control-panel":
    from apps.saas.routers.control_panel import router as cp_router
    app.include_router(cp_router, prefix="/api/v1/saas")

# core_config app
from apps.core_config.router import router as core_config_router
app.include_router(core_config_router, prefix="/api/v1")

# WebSocket — real-time push
from core.api.websocket import router as ws_router
app.include_router(ws_router, prefix="/api/v1")

# Saved filters
from apps.base.saved_filter_router import router as saved_filter_router
app.include_router(saved_filter_router, prefix="/api/v1")

# Dynamic App Discovery & Route Registration
Aras.logic.discovery.register_app_routes(app, prefix="/api/v1")

# Register All Models at Root for Dashboard & UI Compatibility
for model in Aras.Model._registry.values():
    # Ensure RouterFactory has access to Aras
    router = Aras.logic.router_factory.RouterFactory.create_router(model)
    app.include_router(router, prefix="/api/v1")

from pydantic import BaseModel
class ActivateLicenseRequest(BaseModel):
    token: str

license_router = APIRouter(tags=["License"])

@license_router.get("/api/v1/license/status")
async def license_status():
    from core.auth.middleware import get_license_payload, _license_cache, LICENSE_PATH
    import os
    if not os.path.exists(LICENSE_PATH):
        return {"valid": False, "reason": "missing"}
        
    try:
        if _license_cache.get("verified"):
            payload = _license_cache["payload"]
        else:
            payload = get_license_payload()
            
        token = _license_cache.get("token")
        from core.auth.license import days_until_expiry
        days = days_until_expiry(token) if token else 0
        return {
            "valid": True, 
            "tenant_id": payload.get("sub"), 
            "days_remaining": days, 
            "expired": days is not None and days < 0
        }
    except HTTPException as e:
        return {"valid": False, "reason": str(e.detail)}
    except Exception as e:
        return {"valid": False, "reason": str(e)}

@license_router.post("/api/v1/license/activate")
async def activate_license(data: ActivateLicenseRequest, current_user: Any = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    
    from core.auth.middleware import LICENSE_PATH, _license_cache
    import os
    
    os.makedirs(os.path.dirname(LICENSE_PATH), exist_ok=True)
    with open(LICENSE_PATH, "w") as f:
        f.write(data.token)
        
    _license_cache["verified"] = False
    _license_cache["token"] = None
    _license_cache["payload"] = None
    
    return {"status": "success"}

if aras_role != "control-panel":
    app.include_router(license_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to Aras API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/v1/sidebar")
async def get_sidebar_data(_: Any = Depends(get_current_user)):
    """Supplies dynamic navigation data to the frontend."""
    from core.base.app import App
    registered_apps = App._registry

    # 1. Main Navigation Links
    sidebar = [
        {"type": "link", "name": "dashboard", "label": "Dashboard", "icon": "LayoutDashboard", "path": "/dashboard", "have_home": False},
        {"type": "link", "name": "pos", "label": "Point of Sale", "icon": "ShoppingCart", "path": "/pot/pos", "have_home": False},
        {"type": "link", "name": "reports", "label": "Report Center", "icon": "FileBarChart", "path": "/reports", "have_home": False},
        {"type": "link", "name": "settings", "label": "Settings", "icon": "Settings", "path": "/settings", "have_home": False},
        {"type": "link", "name": "help", "label": "Help", "icon": "HelpCircle", "path": "/help", "have_home": False},
    ]

    # 2. Dynamic Apps Organization
    apps_by_name = {}
    root_apps = []

    for _, app_cls in registered_apps.items():
        if app_cls.app_name in ["admin"] or getattr(app_cls, "hide_from_sidebar", False):
            continue
            
        app_data = {
            "type": "app",
            "name": app_cls.app_name,
            "parent_name": getattr(app_cls, "parent_name", ""),
            "label": app_cls.app_label,
            "icon": app_cls.icon,
            "have_home": app_cls.have_home,
            "path": app_cls._get_clean_path(),
            "sub_apps": []
        }
        apps_by_name[app_cls.app_name] = app_data
        
    # Build hierarchy
    for app_name, app_data in apps_by_name.items():
        parent_name = app_data.get("parent_name")
        if parent_name and parent_name in apps_by_name:
            apps_by_name[parent_name]["sub_apps"].append(app_data)
        else:
            root_apps.append(app_data)

    sidebar.extend(root_apps)
    return sidebar


@app.get("/api/v1/app-menu/{app_name:path}")
async def get_app_menu(app_name: str, _: Any = Depends(get_current_user)):
    """Returns app metadata and structured hierarchical menu for the topbar. Supports paths."""
    from core.base.app import App
    
    # Normalize app_name (ensure leading slash and hyphens for matching)
    path = app_name if app_name.startswith("/") else f"/{app_name}"
    path = path.replace("_", "-")
    
    # Find app class by clean path
    app_cls = None
    for _, cls in App._registry.items():
        if cls._get_clean_path() == path:
            app_cls = cls
            break
            
    # Fallback to direct name lookup
    if not app_cls:
        app_cls = App._registry.get(app_name)
            
    if not app_cls:
        return {"error": "App not found"}, 404
        
    # Find sub-apps
    sub_apps = []
    for _, cls in App._registry.items():
        if getattr(cls, "parent_name", None) == app_cls.app_name:
            sub_apps.append({
                "name": cls.app_name,
                "label": cls.app_label,
                "icon": cls.icon,
                "path": cls._get_clean_path(),
                "menu": cls.get_menu_structure()
            })
    
    return {
        "app_name": app_cls.app_name,
        "app_label": app_cls.app_label,
        "icon": app_cls.icon,
        "have_home": app_cls.have_home,
        "menu": app_cls.get_menu_structure(),
        "sub_apps": sub_apps
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
