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
def create_handoff_run(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from core.service_registry import ServiceRegistry
    HandoffRun = ServiceRegistry.get("HandoffRun")
    if HandoffRun is None:
        raise HTTPException(status_code=404, detail="Dev tooling not installed")
    valid = {k: v for k, v in payload.items() if hasattr(HandoffRun, k)}
    run = HandoffRun(**valid)  # type: ignore[arg-type]
    db.add(run)
    db.commit()
    db.refresh(run)
    return run.to_dict()


@router.get("/dev_handoff_runs", response_model=dict)
def list_handoff_runs(
    limit: int = 50,
    sort: str = "id",
    order: str = "desc",
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from core.service_registry import ServiceRegistry
    HandoffRun = ServiceRegistry.get("HandoffRun")
    if HandoffRun is None:
        raise HTTPException(status_code=404, detail="Dev tooling not installed")
    col = getattr(HandoffRun, sort, HandoffRun.id)
    direction = col.desc() if order == "desc" else col.asc()
    runs = db.query(HandoffRun).order_by(direction).limit(limit).all()
    return {"items": [r.to_dict() for r in runs], "total": len(runs)}


@router.patch("/dev_handoff_runs/{run_id}", response_model=dict)
def patch_handoff_run(
    run_id: int,
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    from core.service_registry import ServiceRegistry
    HandoffRun = ServiceRegistry.get("HandoffRun")
    if HandoffRun is None:
        raise HTTPException(status_code=404, detail="Dev tooling not installed")
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


class MetadataFlushRequest(Validation):
    resource: Optional[str] = None


class PermissionSimulateRequest(Validation):
    user_id: int
    resource: str
    action: str


@router.post("/tasks/enqueue")
def enqueue_background_task(
    request: TaskEnqueueRequest,
    _: Any = Depends(require_admin)
):
    """Enqueue a new background task."""
    task_id = TaskManager.enqueue_task(request.task_name, *request.args, **request.kwargs)
    return {"message": "Task enqueued successfully", "task_id": task_id}


@router.get("/tasks/{task_id}/status")
def get_background_task_status(
    task_id: str,
    _: Any = Depends(require_admin)
):
    """Get the status of a background task."""
    return TaskManager.get_task_status(task_id)


@router.post("/sync")
def sync_metadata(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Trigger manual metadata sync."""
    from ..manager.sync_manager import SyncManager
    SyncManager.sync_all(db)
    return {"status": "success", "message": "Metadata synced"}


@router.get("/metadata/flush")
def flush_metadata_cache(_: Any = Depends(require_admin)):
    """Clears the UIGenerator metadata cache."""
    from ..logic.ui_generator import UIGenerator
    UIGenerator.flush_cache()
    return {"status": "success", "message": "Metadata cache flushed"}


@router.post("/metadata/flush")
def flush_metadata_cache_post(
    payload: MetadataFlushRequest,
    _: Any = Depends(require_admin),
):
    """Clears the UIGenerator metadata cache. Resource is accepted for UI intent tracking."""
    from ..logic.ui_generator import UIGenerator
    UIGenerator.flush_cache()
    return {
        "status": "success",
        "resource": payload.resource,
        "message": "Metadata cache flushed",
    }


@router.get("/info")
def get_framework_info(_: Any = Depends(require_admin)):
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
def get_db_stats(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Returns registry statistics."""
    from sqlalchemy import text

    tables = [
        "core_apps", "core_resources", "core_fields",
        "core_links", "core_activity_logs", "core_users",
        "core_roles", "core_permissions", "core_settings",
        "dev_handoff_runs", "dev_template_annotations",
    ]

    # gemini-3-flash-preview
    stats = []
    for table in tables:
        try:
            count = db.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            stats.append({"table": table, "rows": count})
        except Exception:
            stats.append({"table": table, "rows": 0})

    # in-memory error log (not a DB table)
    try:
        from apps.dev.metrics_router import error_log_entries
        stats.append({"table": "dev_error_logs", "rows": len(error_log_entries)})
    except Exception:
        stats.append({"table": "dev_error_logs", "rows": 0})

    return stats


@router.get("/inspect/resource/{resource_name}")
def get_resource_metadata(
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
def inspect_models(_: Any = Depends(require_admin)):
    """Returns all models registered in memory."""
    from ..base.model import Model
    models = []
    for name, cls in sorted(Model._registry.items()):
        table = getattr(cls, "__table__", None)
        columns = []
        relationships = []
        if table is not None:
            for col in table.columns:
                columns.append({
                    "name": col.name,
                    "type": str(col.type),
                    "nullable": bool(col.nullable),
                    "primary_key": bool(col.primary_key),
                    "foreign_keys": [str(fk.column) for fk in col.foreign_keys],
                    "indexed": bool(col.index),
                    "unique": bool(col.unique),
                })
        mapper = getattr(cls, "__mapper__", None)
        if mapper is not None:
            relationships = [
                {
                    "key": rel.key,
                    "target": rel.mapper.class_.__name__,
                    "direction": str(rel.direction).split(".")[-1],
                }
                for rel in mapper.relationships
            ]
        models.append({
            "name": name,
            "class_name": cls.__name__,
            "module": cls.__module__,
            "table": getattr(cls, "__tablename__", None),
            "features": getattr(cls, "__features__", []),
            "scoped_by": getattr(cls, "__scoped_by__", []),
            "route": f"/api/v1/{name.replace('_', '-')}",
            "columns": columns,
            "relationships": relationships,
        })
    return models


@router.get("/inspect/routes")
def inspect_routes(
    request: Request,
    _: Any = Depends(require_admin)
):
    """Returns all registered FastAPI routes."""
    routes = []
    for route in request.app.routes:
        methods = sorted(getattr(route, "methods", set()))
        endpoint = getattr(route, "endpoint", None)
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": methods,
            "tags": list(getattr(route, "tags", []) or []),
            "summary": getattr(route, "summary", None),
            "endpoint": f"{getattr(endpoint, '__module__', '')}.{getattr(endpoint, '__name__', '')}" if endpoint else "",
            "response_model": str(getattr(route, "response_model", "") or ""),
            "auth": "admin" if route.path.startswith("/api/v1/dev") or "/dev/" in route.path else "authenticated",
        })
    return routes


@router.get("/inspect/env")
def inspect_env(_: Any = Depends(require_admin)):
    """Returns basic environment info (sanitized)."""
    import os
    return {
        "cwd": os.getcwd(),
        "python_path": os.getenv("PYTHONPATH", ""),
        "db_url_configured": bool(settings.DATABASE_URL),
        "secret_key_configured": bool(settings.SECRET_KEY),
        "debug": settings.DEBUG,
    }


@router.post("/permissions/simulate")
def simulate_permission(
    payload: PermissionSimulateRequest,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin),
):
    """Explain whether a user can perform an action on a resource."""
    from ..auth.models import User
    from ..logic.permissions import RBAC
    from ..registry.permission import Permission
    from ..registry.role import Role
    from ..registry.user_role import UserRole

    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    action = payload.action.upper()
    resource = payload.resource.strip()
    roles = db.query(Role).join(UserRole, UserRole.role_id == Role.id).filter(UserRole.user_id == user.id).all()
    matches = (
        db.query(Permission, Role)
        .join(Role, Role.id == Permission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id, Permission.resource == resource, Permission.action == action)
        .all()
    )
    allowed = bool(getattr(user, "is_admin", False)) or RBAC.has_permission(db, user, resource, action)
    return {
        "allowed": allowed,
        "user": {"id": user.id, "username": getattr(user, "username", None), "email": getattr(user, "email", None), "is_admin": bool(getattr(user, "is_admin", False))},
        "roles": [{"id": r.id, "name": r.name} for r in roles],
        "resource": resource,
        "action": action,
        "reason": "admin bypass" if getattr(user, "is_admin", False) else ("matching permission" if matches else "no matching role permission"),
        "matches": [{"permission_id": p.id, "role": r.name, "resource": p.resource, "action": p.action} for p, r in matches],
    }

# gemini-flash
@router.get("/dev_template_trees/list")
def list_dev_template_trees(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Returns a list of all template trees."""
    from core.service_registry import ServiceRegistry
    TemplateAnnotation = ServiceRegistry.get("TemplateAnnotation")
    if TemplateAnnotation is None:
        return []
    from sqlalchemy import func
    
    # We want unique template names and their latest update time
    subq = db.query(
        TemplateAnnotation.template_name,
        func.max(TemplateAnnotation.id).label("max_id")
    ).group_by(TemplateAnnotation.template_name).subquery()

    trees = db.query(TemplateAnnotation).join(
        subq, TemplateAnnotation.id == subq.c.max_id
    ).all()

    return [{
        "template_name": tree.template_name,
        "updated_at": tree.updated_at.isoformat() if hasattr(tree, 'updated_at') and tree.updated_at else None
    } for tree in trees]
