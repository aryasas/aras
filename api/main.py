import logging
import os
from pythonjsonlogger.json import JsonFormatter

from fastapi import FastAPI, Depends, HTTPException, Request
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

# Create tables and handle migrations
logger.info("Initializing database schema and running migrations...")
Aras.Base.metadata.create_all(bind=Aras.engine)
Aras.logic.auto_migrate.run(Aras.engine, Aras.Base.metadata)
logger.info("Database schema and migrations complete.")

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    from core.manager.bootstrap import run as bootstrap
    db = next(Aras.get_db())
    Aras.Manager.Audit.register_listeners()
    Aras.Manager.Sync.sync_all(db)
    bootstrap(db)
    yield

app = FastAPI(
    title="Aras API",
    description="Metadata-driven Application Framework powered by FastAPI",
    version="1.0.0",
    lifespan=lifespan
)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning("HTTP Exception: %s", exc.detail, extra={"status_code": exc.status_code, "path": request.url.path})
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "code": exc.status_code
        },
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled Exception: %s", exc, extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected internal server error occurred.",
            "detail": str(exc) if settings.DEBUG else "Please contact administrator",
            "code": 500
        },
    )

# Rate limiting — must be added before CORS so it applies to all routes
from core.lib.rate_limiter import RateLimiterMiddleware
app.add_middleware(RateLimiterMiddleware)

# CORS — allow_origins=["*"] + allow_credentials=True violates the spec and is rejected by browsers
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# Core Routes
from core.auth.routes import router as auth_router
from core.auth.service import get_current_user
app.include_router(auth_router, prefix="/api/v1")

# Tier 2 API Routers
app.include_router(Aras.api.query.router, prefix="/api/v1")
app.include_router(Aras.api.workflow.router, prefix="/api/v1")
app.include_router(Aras.api.admin.router, prefix="/api/v1/admin")
app.include_router(Aras.api.dev.router, prefix="/api/v1/dev")
app.include_router(Aras.api.registry.router, prefix="/api/v1")
app.include_router(Aras.api.files.router, prefix="/api/v1")
app.include_router(Aras.api.dashboard.router, prefix="/api/v1")

# WebSocket — real-time push
from core.api.websocket import router as ws_router
app.include_router(ws_router, prefix="/api/v1")

# Dynamic App Discovery & Route Registration
Aras.logic.discovery.register_app_routes(app, prefix="/api/v1")

# Register Core Models at Root for UI Compatibility
core_models = [
    Aras.User, Aras.Role, Aras.Permission, Aras.ActivityLog, Aras.ArasSetting,
    Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel, Aras.TranslationModel,
    Aras.WidgetModel, Aras.DashboardLayoutModel,
    Aras.logic.discovery.load_class("core.registry.series.Series")
]
for model in core_models:
    # Ensure RouterFactory has access to Aras
    router = Aras.logic.router_factory.RouterFactory.create_router(model)
    app.include_router(router, prefix="/api/v1")

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
        {"type": "link", "name": "settings", "label": "Settings", "icon": "Settings", "path": "/settings", "have_home": False},
    ]

    # 2. Dynamic Apps Organization
    apps_by_name = {}
    root_apps = []

    for _, app_cls in registered_apps.items():
        if app_cls.app_name in ["admin"]:
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
