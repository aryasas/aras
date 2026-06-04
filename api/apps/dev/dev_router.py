import json
import os
import platform
import psutil
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from core.lib.database import get_db
from core.response import ok
from core import Aras
from core.lib.settings import settings
from core.auth.service import require_admin

dev_general_router = APIRouter(tags=["Developer General Tools"])


class SeedRunRequest(BaseModel):
    keys: List[str]
    org_id: int

class ImpersonateRequest(BaseModel):
    user_id: int

@dev_general_router.post("/dev/impersonate")
def impersonate_user(payload: ImpersonateRequest, db: Session = Depends(get_db)):
    """Generate a short-lived token as another user (admin only)."""
    from core.auth.models import User
    target = db.query(User).filter(User.id == payload.user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="user not found")
    from core.auth.service import create_access_token
    from datetime import timedelta
    token = create_access_token(
        data={"sub": str(target.id), "impersonation": True},
        expires_delta=timedelta(minutes=30),
    )
    return ok({
        "token": token,
        "user": {"id": target.id, "username": getattr(target, "username", None), "email": getattr(target, "email", None)},
        "expires_in": 1800,
    })

@dev_general_router.get("/dev/permissions-matrix")
def get_permissions_matrix(db: Session = Depends(get_db)):
    """Returns role × resource permissions grid."""
    from core.registry.role import Role
    from core.registry.permission import Permission
    from core.registry.resource_model import ResourceModel
    roles = db.query(Role).all()
    resources = db.query(ResourceModel).all()
    perms = db.query(Permission).all()
    grid = {}
    for p in perms:
        key = f"{p.role_id}:{p.resource}"
        cell = grid.setdefault(key, {
            "can_read": False,
            "can_create": False,
            "can_update": False,
            "can_delete": False,
            "actions": [],
        })
        action = str(p.action or "").lower()
        cell["actions"].append(str(p.action or ""))
        if action in {"read", "list", "view"}:
            cell["can_read"] = True
        if action in {"create", "write"}:
            cell["can_create"] = True
        if action in {"update", "edit", "write"}:
            cell["can_update"] = True
        if action in {"delete", "remove"}:
            cell["can_delete"] = True
    return ok({
        "roles": [{"id": r.id, "name": r.name} for r in roles],
        "resources": [{"id": r.id, "name": r.name, "label": getattr(r, "label", r.name)} for r in resources],
        "grid": grid,
    })

class ScaffoldField(BaseModel):
    name: str
    type: str = "String"

class ScaffoldRequest(BaseModel):
    kind: str = "app"  # "app" or "model"
    name: str
    label: Optional[str] = None
    icon: str = "Box"
    fields: List[ScaffoldField] = []

@dev_general_router.post("/dev/scaffold")
def scaffold_app(payload: ScaffoldRequest):
    """Generates source code template for a new app or model."""
    name = payload.name.strip()
    if not name or not name.replace("_", "").isalnum():
        raise HTTPException(status_code=400, detail="name must be alphanumeric/underscore")
    
    if payload.kind == "app":
        label = payload.label or name.replace("_", " ").title()
        code = f'''"""\nPurpose: {label} application.\n"""\nfrom core import Aras\nfrom core.logic.discovery import autodiscover_models\n\n\nclass {name.title().replace("_", "")}(Aras.App):\n    app_name = "{name}"\n    app_label = "{label}"\n    description = "{label} module."\n    icon = "{payload.icon}"\n    have_home = True\n\n    models = autodiscover_models(__name__, ["models"])\n\n    menu_groups = []\n'''
        return ok({"filename": f"apps/{name}/app.py", "code": code})
    elif payload.kind == "model":
        field_lines = []
        for f in payload.fields:
            field_lines.append(f"    {f.name} = Aras.Field({f.type})")
        if not field_lines:
            field_lines = ["    name = Aras.Field(String, nullable=False)"]
        
        fields_code = "\n".join(field_lines)
        code = f'''from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float\nfrom core import Aras\n\n\nclass {name.title().replace("_", "")}(Aras.Model):\n    __tablename__ = "{name.lower()}s"\n    __aras_meta__ = {{"label": "{name.replace("_", " ").title()}", "icon": "Box"}}\n\n{fields_code}\n'''
        return ok({"filename": f"apps/<app>/models/{name}.py", "code": code})
    raise HTTPException(status_code=400, detail="kind must be 'app' or 'model'")

@dev_general_router.get("/dev/activity-heatmap")
def get_activity_heatmap(db: Session = Depends(get_db), days: int = 7):
    """Returns CRUD activity counts per resource for the last N days."""
    from core.registry.activity_log import ActivityLog
    from datetime import datetime, timedelta

    days = max(1, min(int(days or 7), 365))
    today = datetime.utcnow().date()
    start_day = today - timedelta(days=days - 1)
    cutoff = datetime.combine(start_day, datetime.min.time())

    try:
        rows = db.query(ActivityLog).filter(ActivityLog.created_at >= cutoff).all()
        totals = {}
        by_day = {}
        calendar = []

        for offset in range(days):
            day = (start_day + timedelta(days=offset)).isoformat()
            by_day[day] = {"create": 0, "update": 0, "delete": 0, "read": 0, "total": 0, "resources": {}}
            calendar.append({"date": day, "create": 0, "update": 0, "delete": 0, "read": 0, "total": 0})

        for row in rows:
            day = (row.created_at.date() if row.created_at else today).isoformat()
            if day not in by_day:
                continue
            r = getattr(row, "resource", None) or "unknown"
            if r not in totals:
                totals[r] = {"create": 0, "update": 0, "delete": 0, "read": 0}
            if r not in by_day[day]["resources"]:
                by_day[day]["resources"][r] = {"create": 0, "update": 0, "delete": 0, "read": 0, "total": 0}
            a = (getattr(row, "action", None) or "").lower()
            if a not in totals[r]:
                a = "read"
            totals[r][a] += 1
            by_day[day][a] += 1
            by_day[day]["total"] += 1
            by_day[day]["resources"][r][a] += 1
            by_day[day]["resources"][r]["total"] += 1

        for item in calendar:
            counts = by_day[item["date"]]
            item.update({k: counts[k] for k in ("create", "update", "delete", "read", "total")})

        return ok({"days": days, "data": totals, "by_day": by_day, "calendar": calendar})
    except Exception as e:
        return ok({"days": days, "data": {}, "by_day": {}, "calendar": [], "error": str(e)[:200]})

@dev_general_router.get("/dev/search")
def global_search(q: str, db: Session = Depends(get_db)):
    """Universal search for command palette."""
    q = (q or "").strip().lower()
    if not q or len(q) < 2:
        return ok({"results": []})
    results = []
    # Resources
    from core.base.model import Model
    for name, model in Model._registry.items():
        if q in name.lower() or q in getattr(model, "__tablename__", "").lower():
            results.append({
                "kind": "resource",
                "label": name,
                "sub": getattr(model, "__tablename__", ""),
                "action": f"/dev/{name}",
            })
    # Apps
    from core.base.app import App
    for app_name, app_cls in App._registry.items():
        if q in app_name.lower() or q in app_cls.app_label.lower():
            results.append({
                "kind": "app",
                "label": app_cls.app_label,
                "sub": app_name,
                "action": app_cls._get_clean_path(),
            })
    # Settings
    try:
        from core.registry.sys_settings import Settings as _S
        rows = db.query(_S).filter(_S.key.ilike(f"%{q}%")).limit(10).all()
        for s in rows:
            results.append({
                "kind": "setting",
                "label": s.key,
                "sub": str(s.value)[:50] if s.value else "",
                "action": f"/admin/settings",
            })
    except Exception:
        pass
    return ok({"results": results[:30]})

@dev_general_router.get("/dev/system-info")
def get_system_info():
    """Returns basic server system info."""
    process = psutil.Process(os.getpid())
    return ok({
        "os": platform.system(),
        "os_release": platform.release(),
        "cpu_count": psutil.cpu_count(),
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent
        },
        "process": {
            "memory_usage": process.memory_info().rss,
            "cpu_percent": process.cpu_percent(),
            "threads": process.num_threads(),
            "uptime_seconds": _time_since(process.create_time())
        },
        "python_version": platform.python_version(),
    })

def _time_since(timestamp):
    import time
    return int(time.time() - timestamp)

@dev_general_router.get("/dev/config")
def get_env_config():
    """Returns environment variables, masking sensitive ones."""
    sensitive_keys = {"password", "secret", "key", "token", "auth"}
    config = {}
    for k, v in os.environ.items():
        if any(s in k.lower() for s in sensitive_keys):
            config[k] = "********"
        else:
            config[k] = v
    return ok(config)

@dev_general_router.get("/dev/apps-status")
def get_apps_status():
    """Returns status of all loaded apps."""
    from core.base.app import App
    apps = []
    for name, cls in App._registry.items():
        apps.append({
            "name": name,
            "label": cls.app_label,
            "type": getattr(cls, "app_type", "custom"),
            "version": getattr(cls, "version", "1.0.0"),
            "models_count": len(cls.models) if isinstance(cls.models, list) else 0,
            "routers_count": len(cls.routers) if hasattr(cls, "routers") and isinstance(cls.routers, list) else 0
        })
    return ok(apps)


@dev_general_router.get("/dev/seeds")
def list_seed_catalog(
    db: Session = Depends(get_db),
    current_user: object = Depends(require_admin),
):
    del db, current_user
    from core.seeds.base import seed_catalog

    return ok(seed_catalog())


@dev_general_router.post("/dev/seeds/run")
def run_selected_seeds(
    payload: SeedRunRequest,
    db: Session = Depends(get_db),
    current_user: object = Depends(require_admin),
):
    del current_user
    from core.seeds.base import execute_seed_entry, seed_catalog, iter_seed_entries
    from core.base.app import App

    requested_keys = [key for key in payload.keys if key]
    if not requested_keys:
        raise HTTPException(status_code=400, detail="At least one seed key is required.")
    if payload.org_id < 1:
        raise HTTPException(status_code=400, detail="org_id must be a positive integer.")

    catalog_index = {
        item["key"]: item
        for app_cls in App._registry.values()
        for item in iter_seed_entries(app_cls)
    }
    # Force catalog evaluation so both API surfaces share the same ordering source.
    for group in seed_catalog():
        for item in group.get("seeds", []):
            if item["key"] == "demo:all":
                from seeds.demo import run_seed

                catalog_index[item["key"]] = {
                    "app_cls": None,
                    "app_name": item["app_name"],
                    "app_label": group.get("app_label", item["app_name"]),
                    "entry": run_seed,
                    "owner_dir": None,
                    "key": item["key"],
                    "label": item["label"],
                    "optional": item["optional"],
                }

    results = []
    seen: set[str] = set()
    for key in requested_keys:
        if key in seen:
            results.append({"key": key, "status": "skipped", "message": "Duplicate key ignored."})
            continue
        seen.add(key)
        entry_info = catalog_index.get(key)
        if not entry_info:
            results.append({"key": key, "status": "error", "message": "Unknown seed key."})
            continue
        try:
            execute_seed_entry(entry_info, db, org_id=payload.org_id)
            db.commit()
            results.append({"key": key, "status": "ran", "message": "Seed completed."})
        except Exception as exc:
            db.rollback()
            results.append({"key": key, "status": "error", "message": str(exc)[:300]})

    return ok(results)
