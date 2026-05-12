import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from core import Aras
from core.lib.database import get_db

router = APIRouter(tags=["Developer Tools"])

@router.post("/sync")
async def sync_metadata(db: Session = Depends(get_db)):
    """
    Force synchronization of code-defined models to the database registry.
    """
    try:
        Aras.Manager.Sync.sync_all(db)
        return {"status": "success", "message": "Metadata synchronization completed."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")

@router.get("/info")
async def get_framework_info():
    """
    Return basic information about the framework.
    """
    return {
        "version": "1.0.0",
        "engine": "Aras Metadata Engine",
        "apps_discovered": list(Aras.App._registry.keys()),
        "total_models": sum(len(app.models) for app in Aras.App._registry.values())
    }

@router.get("/db-stats")
async def get_db_stats(db: Session = Depends(get_db)):
    """
    Get basic database statistics.
    """
    from sqlalchemy import text
    tables = Aras.Base.metadata.tables.keys()
    stats = []
    for table in tables:
        try:
            count = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            stats.append({"table": table, "rows": count})
        except:
            stats.append({"table": table, "rows": "error"})
    
    return stats

@router.get("/resources/{resource_name}/metadata")
async def get_resource_metadata(resource_name: str, db: Session = Depends(get_db)):
    """
    Get full metadata for a resource from the DB registry (Resource, Fields, Links).
    """
    from core.registry.resource_model import ResourceModel
    from core.registry.field_model import FieldModel
    from core.registry.link_model import LinkModel

    resource = db.query(ResourceModel).filter(ResourceModel.name == resource_name).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found in registry")

    fields = db.query(FieldModel).filter(FieldModel.resource_id == resource.id).all()
    links = db.query(LinkModel).filter(
        (LinkModel.source_resource_id == resource.id) | 
        (LinkModel.target_resource_id == resource.id)
    ).all()

    return {
        "resource": resource.to_dict(),
        "fields": [f.to_dict() for f in fields],
        "links": [l.to_dict() for l in links]
    }

@router.get("/inspect/models")
async def inspect_models():
    """
    Advanced inspection of all registered models and their attributes.
    """
    inspection = {}
    for app_name, app_cls in Aras.App._registry.items():
        inspection[app_name] = []
        for model in app_cls.models:
            model_info = {
                "name": model.__name__,
                "table": getattr(model, "__tablename__", "N/A"),
                "columns": [c.name for c in model.__table__.columns] if hasattr(model, "__table__") else [],
                "traits": [t.__name__ for t in model.__bases__ if hasattr(t, "__name__")]
            }
            inspection[app_name].append(model_info)
    return inspection

@router.get("/inspect/routes")
async def inspect_routes(request: Request):
    """
    List all API routes registered in the framework.
    """
    routes = []
    for route in request.app.routes:
        if hasattr(route, "path"):
            routes.append({
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods) if hasattr(route, "methods") else []
            })
    return routes

@router.get("/inspect/env")
async def inspect_env():
    """
    List key environment variables for debugging.
    """
    # Only expose safe configuration variables
    safe_prefixes = ("ARAS_", "DB_", "APP_")
    env = {k: v for k, v in os.environ.items() if k.startswith(safe_prefixes) or k in ["DEBUG", "PORT", "DATABASE_URL"]}
    
    # Redact sensitive info if it looks like a password
    for k in env:
        if any(secret in k.lower() for secret in ["pass", "key", "token", "secret"]):
            env[k] = "********"
            
    return env
