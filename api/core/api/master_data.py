# gemini-flash
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..lib.database import get_db
from ..auth.service import get_current_user
from ..registry.master_data_registry import master_data_registry, MasterEntity

router = APIRouter(prefix="/master-data", tags=["Master Data"])

def _check_master_data_permission(db: Session, user: Any, entity_key: str, action: str) -> bool:
    """
    Checks if user has permission for a master data entity.
    RBAC: master_data:{key}:{action}
    Falls back to underlying model's resource permission if no specific grant.
    """
    from ..logic.permissions import RBAC
    # 1. Check specific master_data permission
    permission_key = f"master_data:{entity_key}"
    action_upper = action.upper()
    if RBAC.has_permission(db, user, permission_key, action_upper):
        return True

    # 2. Fallback to model resource permission
    entity = master_data_registry.get_by_key(entity_key)
    if not entity:
        return False

    model_table = getattr(entity.model, "__tablename__", None)
    if model_table and RBAC.has_permission(db, user, model_table, action_upper):
        return True

    return False

def _get_resource_url(app_name: str, model_cls: Any) -> str:
    """Resolves the resource URL for a model based on its app registration."""
    from ..aras import Aras
    apps = Aras.get_registered("App")
    app_cls = apps.get(app_name)
    # If the registration's app_name doesn't own the model (e.g. core master_data
    # entries pointing at models actually owned by the `config` app), search all
    # apps for the model so the URL matches the actually-mounted route.
    if not app_cls or model_cls not in getattr(app_cls, "models", []):
        for candidate in apps.values():
            if model_cls in getattr(candidate, "models", []):
                app_cls = candidate
                break
    if not app_cls:
        return f"/api/v1/{model_cls.__tablename__.replace('_', '-')}"
    
    app_path = app_cls._get_clean_path()
    
    # Mirror logic from discovery.register_app_routes
    model_seg = model_cls.__tablename__
    full_prefix = f"{app_cls.parent_name}_{app_cls.app_name}_" if app_cls.parent_name and app_cls.app_name else None
    
    if app_cls.table_prefix and model_seg.startswith(f"{app_cls.table_prefix}_"):
        model_seg = model_seg[len(app_cls.table_prefix)+1:]
    elif full_prefix and model_seg.startswith(full_prefix):
        model_seg = model_seg[len(full_prefix):]
    elif app_cls.app_name and model_seg.startswith(f"{app_cls.app_name}_"):
        model_seg = model_seg[len(app_cls.app_name)+1:]
    elif app_cls.parent_name and model_seg.startswith(f"{app_cls.parent_name}_"):
        model_seg = model_seg[len(app_cls.parent_name)+1:]
    
    model_path = f"/{model_seg.replace('_', '-')}"
    return f"/api/v1{app_path}{model_path}"

@router.get("")
def list_entities(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """Returns list of master data entities the user can read."""
    results = []
    # Deduplicate by key (in case core and config both register)
    seen_keys = set()
    
    for entity in master_data_registry.all():
        if entity.key in seen_keys or entity.hidden:
            continue
            
        if not _check_master_data_permission(db, user, entity.key, "read"):
            continue
            
        model_table = getattr(entity.model, "__tablename__", "")
        resource_url = _get_resource_url(entity.app_name, entity.model)
        
        results.append({
            "key": entity.key,
            "label": entity.label,
            "icon": entity.icon,
            "scope": entity.scope,
            "app": entity.app_name,
            "resource": model_table,
            "model_table": model_table,
            "resource_url": resource_url,
            "can_write": _check_master_data_permission(db, user, entity.key, "write"),
            "can_admin": _check_master_data_permission(db, user, entity.key, "admin"),
            "help": entity.help,
            "order": entity.order
        })
        seen_keys.add(entity.key)
    
    return sorted(results, key=lambda x: (x["scope"] != "shared", x["order"], x["label"]))

@router.get("/schema")
def get_schema(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """Returns registry payload grouped by scope/app for the UI rail."""
    entities = list_entities(db, user)
    
    groups = []
    
    # 1. Shared Group (scope=shared)
    shared = [e for e in entities if e["scope"] == "shared"]
    if shared:
        groups.append({
            "key": "shared",
            "label": "Shared",
            "entities": sorted(shared, key=lambda x: (x["order"], x["label"]))
        })
        
    # 2. Per-App Groups
    apps_list = []
    seen_apps = set()
    for e in entities:
        if e["scope"] != "shared" and e["app"] not in seen_apps and e["app"] != "core":
            apps_list.append(e["app"])
            seen_apps.add(e["app"])
            
    from ..aras import Aras
    for app_name in sorted(apps_list):
        app_entities = [e for e in entities if e["app"] == app_name and e["scope"] != "shared"]
        if app_entities:
            app_cls = Aras.get_registered("App").get(app_name)
            label = getattr(app_cls, "app_label", app_name.title())
            groups.append({
                "key": app_name,
                "label": label,
                "entities": sorted(app_entities, key=lambda x: (x["order"], x["label"]))
            })
            
    return {"groups": groups}
