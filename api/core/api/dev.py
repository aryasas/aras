import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..lib.database import get_db
from ..lib.settings import settings
from ..auth.service import require_admin
from ..manager.task_manager import TaskManager
from ..base.validation import Validation

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Developer Tools"])


# ── Handoff Runs CRUD ────────────────────────────────────────────────────────

@router.post("/dev_handoff_runs", response_model=dict, status_code=201)
async def create_handoff_run(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from apps.dev.models import HandoffRun
    valid = {k: v for k, v in payload.items() if hasattr(HandoffRun, k)}
    run = HandoffRun(**valid)  # type: ignore[arg-type]
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.to_dict()


@router.get("/dev_handoff_runs", response_model=dict)
async def list_handoff_runs(
    limit: int = 50,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from apps.dev.models import HandoffRun
    runs = db.query(HandoffRun).order_by(HandoffRun.id.desc()).limit(limit).all()
    return {"items": [r.to_dict() for r in runs], "total": len(runs)}


@router.patch("/dev_handoff_runs/{run_id}", response_model=dict)
async def patch_handoff_run(
    run_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from apps.dev.models import HandoffRun
    run = db.get(HandoffRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    for k, v in payload.items():
        if hasattr(run, k):
            setattr(run, k, v)
    db.commit()
    db.refresh(run)
    return run.to_dict()


class TaskEnqueueRequest(Validation):
    task_name: str
    args: Optional[List[Any]] = []
    kwargs: Optional[Dict[str, Any]] = {}


@router.post("/tasks/enqueue")
async def enqueue_background_task(
    request: TaskEnqueueRequest,
    _: Any = Depends(require_admin)
):
    """Enqueue a new background task."""
    task_id = TaskManager.enqueue_task(request.task_name, *request.args, **request.kwargs)
    return {"message": "Task enqueued successfully", "task_id": task_id}


@router.get("/tasks/{task_id}/status")
async def get_background_task_status(
    task_id: str,
    _: Any = Depends(require_admin)
):
    """Get the status of a background task."""
    return TaskManager.get_task_status(task_id)


@router.post("/sync")
async def sync_metadata(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Trigger manual metadata sync."""
    from ..manager.sync_manager import SyncManager
    SyncManager.sync_all(db)
    return {"status": "success", "message": "Metadata synced"}


@router.get("/info")
async def get_framework_info(_: Any = Depends(require_admin)):
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
async def get_db_stats(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
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
            stats.append({"table": table, "rows": 0})

    return stats


@router.get("/inspect/resource/{resource_name}")
async def get_resource_metadata(
    resource_name: str,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Get full metadata for a resource from the DB registry."""
    from ..registry.resource_model import ResourceModel

    res = db.query(ResourceModel).filter(ResourceModel.name == resource_name).first()
    if not res:
        raise HTTPException(status_code=404, detail="Resource not found")

    return {
        "resource": res.to_dict(),
        "fields": [f.to_dict() for f in res.fields],
        "links": [l.to_dict() for l in res.links]
    }


@router.get("/inspect/models")
async def inspect_models(_: Any = Depends(require_admin)):
    """Returns all models registered in memory."""
    from ..base.model import Model
    return {name: str(cls) for name, cls in Model._registry.items()}


@router.get("/inspect/routes")
async def inspect_routes(
    request: Request,
    _: Any = Depends(require_admin)
):
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
async def inspect_env(_: Any = Depends(require_admin)):
    """Returns basic environment info (sanitized)."""
    import os
    return {
        "cwd": os.getcwd(),
        "python_path": os.getenv("PYTHONPATH", ""),
        "db_url_configured": bool(settings.DATABASE_URL),
        "secret_key_configured": bool(settings.SECRET_KEY),
        "debug": settings.DEBUG,
    }
