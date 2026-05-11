from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import uvicorn

from core import Aras
from core.auth import router as auth_router
from core.lib.discovery import discover_apps, register_app_routes
from core.lib.auto_migrate import run as auto_migrate

# Discover and load all apps
discover_apps(package_path="apps")

# Create tables and handle migrations
Aras.Base.metadata.create_all(bind=Aras.engine)
auto_migrate(Aras.engine, Aras.Base.metadata)

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
app.include_router(auth_router, prefix="/api/v1")

# Dynamic App Discovery & Route Registration
register_app_routes(app, prefix="/api/v1")

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
    registered_apps = Aras.get_registered("app")
    sidebar = []

    for app_name, app_cls in registered_apps.items():
        sidebar.append({
            "name": app_cls.app_name,
            "label": app_cls.app_label,
            "icon": app_cls.icon,
            "models": [
                {
                    "name": m.__tablename__,
                    "label": getattr(m, "__title__", m.__tablename__.replace("_", " ").title())
                } for m in app_cls.models
            ]
        })
    return sidebar

@app.on_event("startup")
def seed_data():
    db = next(Aras.get_db())

    # Seed Admin
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
    from apps.system.models import ArasSetting
    defaults = [
        {"key": "app_name", "value": "Aras ERP", "description": "Application display name"},
        {"key": "maintenance_mode", "value": "false", "description": "Disable public access"},
        {"key": "default_language", "value": "en", "description": "System-wide default language"},
    ]
    for d in defaults:
        if not db.query(ArasSetting).filter(ArasSetting.key == d["key"]).first():
            print(f"Seeding setting: {d['key']}")
            db.add(ArasSetting(**d))
    db.commit()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
