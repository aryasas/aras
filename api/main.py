from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from core import Aras

# Discover and load all apps
Aras.logic.discovery.discover_apps(package_path="apps")

# Create tables and handle migrations
Aras.Base.metadata.create_all(bind=Aras.engine)
Aras.logic.auto_migrate.run(Aras.engine, Aras.Base.metadata)

app = FastAPI(
    title="Aras API",
    description="Metadata-driven ERP Engine powered by FastAPI",
    version="1.0.0"
)

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
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
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "An unexpected internal server error occurred.",
            "detail": str(exc) if app.debug else "Please contact administrator",
            "code": 500
        },
    )

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core Routes
from core.auth.routes import router as auth_router
app.include_router(auth_router, prefix="/api/v1")

# Tier 2 API Routers
app.include_router(Aras.api.query.router, prefix="/api/v1")
app.include_router(Aras.api.workflow.router, prefix="/api/v1")
app.include_router(Aras.api.admin.router, prefix="/api/v1/admin")
app.include_router(Aras.api.dev.router, prefix="/api/v1/dev")
app.include_router(Aras.api.registry.router, prefix="/api/v1")

# Dynamic App Discovery & Route Registration
Aras.logic.discovery.register_app_routes(app, prefix="/api/v1")

# Register Core Models at Root for UI Compatibility
core_models = [
    Aras.User, Aras.Role, Aras.Permission, Aras.ActivityLog, Aras.ArasSetting,
    Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel, Aras.TranslationModel
]
for model in core_models:
    router = Aras.Router(model)
    app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Welcome to Aras API",
        "status": "online",
        "docs": "/docs"
    }

@app.get("/api/v1/sidebar")
async def get_sidebar_data():
    """
    Endpoint untuk menyuplai data menu ke frontend secara dinamis.
    """
    from core.base.app import App
    registered_apps = App._registry

    # 1. Main Navigation Links
    sidebar = [
        {"type": "link", "name": "dashboard", "label": "Dashboard", "icon": "LayoutDashboard", "path": "/"},
        {"type": "link", "name": "settings", "label": "Settings", "icon": "Settings", "path": "/settings"},
    ]

    # 2. Dynamic Apps
    apps_group = []
    for app_name, app_cls in registered_apps.items():
        if app_name in ["admin"]:
            continue

        models_list = []

        # Inject special pages
        if app_name == "dev":
            models_list.append({"name": "dev-home", "label": "Dev Home", "path": "/dev"})

        models_list.extend([
            {
                "name": m.__tablename__,
                "label": getattr(m, "__title__", m.__tablename__.replace("_", " ").title()),
                "path": f"/{app_cls.app_name}/{m.__tablename__}"
            } for m in app_cls.models if m.__tablename__ not in ["auth_users", "sys_settings"]
        ])

        apps_group.append({
            "type": "app",
            "name": app_cls.app_name,
            "label": app_cls.app_label,
            "icon": app_cls.icon,
            "models": models_list
        })

    sidebar.extend(apps_group)

    return sidebar
@app.on_event("startup")
def startup_event():
    db = next(Aras.get_db())

    # 1. Register Global Listeners
    Aras.Manager.Audit.register_listeners()

    # 2. Sync Metadata (Code -> DB Registry)
    Aras.Manager.Sync.sync_all(db)

    # 2. Seed Admin
    admin = db.query(Aras.User).filter(Aras.User.username == "admin").first()
    if not admin:
        print("Creating default admin user...")
        new_admin = Aras.User(
            username="admin",
            email="admin@aras.local",
            password_hash=Aras.User.hash_password("admin"),
            is_admin=True
        )
        db.add(new_admin)
        db.commit()
        print("Admin user created (admin/admin)")

    # Seed Settings
    from core.registry.sys_settings import ArasSetting
    defaults = [
        {"key": "app_name", "value": "Aras ERP", "description": "Application display name"},
        {"key": "maintenance_mode", "value": "false", "description": "Disable public access"},
        {"key": "default_language", "value": "en", "description": "System-wide default language"},
        {"key": "core.date_format", "value": "YYYY-MM-DD", "description": "Global date format"},
        {"key": "core.number_format", "value": "#,###.##", "description": "Global number format"},
        {"key": "core.decimal_precision", "value": "2", "description": "Global decimal precision"},
        {"key": "core.currency_symbol", "value": "$", "description": "Global currency symbol"},
        {"key": "core.language_default", "value": "en", "description": "Global default language"},
    ]
    for d in defaults:
        if not db.query(ArasSetting).filter(ArasSetting.key == d["key"]).first():
            print(f"Seeding setting: {d['key']}")
            db.add(ArasSetting(**d))
    db.commit()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
