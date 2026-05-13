from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..aras import Aras
from ..lib.database import get_db
from ..manager.task_manager import TaskManager # Import TaskManager

router = APIRouter(tags=["Developer Tools"])

class TaskEnqueueRequest(BaseModel):
    task_name: str
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}

@router.post("/tasks/enqueue")
async def enqueue_background_task(request: TaskEnqueueRequest):
    """Enqueue a new background task."""
    task_id = TaskManager.enqueue_task(request.task_name, *request.args, **request.kwargs)
    return {"message": "Task enqueued successfully", "task_id": task_id}

@router.get("/tasks/{task_id}/status")
async def get_background_task_status(task_id: str):
    """Get the status of a background task."""
    status = TaskManager.get_task_status(task_id)
    return status

@router.post("/sync")
async def sync_metadata(db: Session = Depends(get_db)):
    """Trigger manual metadata sync."""
    from ..manager.sync_manager import SyncManager
    SyncManager.sync_all(db)
    return {"status": "success", "message": "Metadata synced"}

@router.get("/info")
async def get_framework_info(db: Session = Depends(get_db)):
    """Returns framework version and basic stats."""
    from ..base.app import App
    from ..base.model import Model
    return {
        "framework": "Aras",
        "version": "1.0.0",
        "engine": "FastAPI + SQLAlchemy",
        "apps_discovered": list(App._registry.keys()),
        "total_models": len(Model._registry)
    }

@router.get("/stats")
async def get_db_stats(db: Session = Depends(get_db)):
    """Returns registry statistics."""
    from sqlalchemy import text
    
    tables = [
        "aras_apps", "aras_resources", "aras_fields", 
        "aras_links", "aras_activity_logs", "auth_users", 
        "auth_roles", "auth_permissions", "sys_settings"
    ]
    
    stats = []
    for table in tables:
        try:
            count = db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            stats.append({"table": table, "rows": count})
        except Exception:
            # Table might not exist yet
            stats.append({"table": table, "rows": 0})
            
    return stats

@router.get("/inspect/resource/{resource_name}")
async def get_resource_metadata(resource_name: str, db: Session = Depends(get_db)):
    """
    Get full metadata for a resource from the DB registry (Resource, Fields, Links).
    """
    from ..registry.resource_model import ResourceModel
    from ..registry.field_model import FieldModel
    from ..registry.link_model import LinkModel

    res = db.query(ResourceModel).filter(ResourceModel.name == resource_name).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    return {
        "resource": res.to_dict(),
        "fields": [f.to_dict() for f in res.fields],
        "links": [l.to_dict() for l in res.links]
    }

@router.get("/inspect/models")
async def inspect_models():
    """Returns all models registered in memory."""
    from ..base.model import Model
    return {name: str(cls) for name, cls in Model._registry.items()}

@router.get("/inspect/routes")
async def inspect_routes(request: Request):
    """Returns all registered FastAPI routes."""
    routes = []
    for route in request.app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods)
        })
    return routes

@router.get("/inspect/env")
async def inspect_env():
    """Returns basic environment info (Sanitized)."""
    import os
    return {
        "cwd": os.getcwd(),
        "python_path": os.getenv("PYTHONPATH", ""),
        "db_url_configured": bool(os.getenv("SQLALCHEMY_DATABASE_URI"))
    }
