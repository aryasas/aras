# gemini-flash
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, Dict

from ..lib.database import get_db
from ..auth.service import get_current_user
from ..logic.permissions import RBAC
from ..registry.settings_service import SettingsService
from ..registry.config_registry import config_registry
from ..response import ok, err

router = APIRouter(prefix="/settings", tags=["Settings"])

def _check_settings_permission(db: Session, user: Any, namespace: str, action: str):
    if user.is_admin:
        return True
    
    # Check for settings:admin (cross-namespace)
    if RBAC.has_permission(db, user, "settings", "ADMIN"):
        return True
        
    # Check for generic settings access
    if RBAC.has_permission(db, user, "settings", action.upper()):
        return True

    # Check for settings:read/write per namespace
    resource = f"settings:{namespace}"
    if RBAC.has_permission(db, user, resource, action.upper()):
        return True
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=f"Not enough permissions to {action} settings for {namespace}"
    )

@router.get("")
def list_namespaces(db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    """Returns a list of namespaces that the user has READ access to."""
    from ..base.app import App
    
    namespaces = []
    registered_apps = {app_cls.app_name: app_cls for app_cls in App._registry.values()}

    all_namespaces = sorted({ns for (ns, _key) in getattr(config_registry, "_entries", {}).keys()})
    if not all_namespaces:
        all_namespaces = sorted(set(registered_apps.keys()) | {"core"})

    framework_meta = {
        "core": {"label": "Framework", "icon": "Settings"},
    }

    for ns in all_namespaces:
        sections = config_registry.by_app(ns)
        if not sections:
            continue
        try:
            _check_settings_permission(db, user, ns, "read")
        except HTTPException:
            continue
        if ns in registered_apps:
            app_cls = registered_apps[ns]
            label = app_cls.app_label or ns.title()
            icon = getattr(app_cls, "icon", "Box") or "Box"
        else:
            meta = framework_meta.get(ns, {"label": ns.title(), "icon": "Box"})
            label = meta["label"]
            icon = meta["icon"]
        namespaces.append({"name": ns, "label": label, "icon": icon})

    return ok(namespaces)

@router.get("/{namespace}")
def get_namespace_settings(namespace: str, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    """Returns all settings for a namespace."""
    _check_settings_permission(db, user, namespace, "read")
    
    reveal_secrets = user.is_admin or RBAC.has_permission(db, user, "settings", "ADMIN")
    settings = SettingsService.all(db, namespace, reveal_secrets=reveal_secrets)
    return ok(settings)

@router.put("/{namespace}")
def update_namespace_settings(namespace: str, values: Dict[str, Dict[str, Any]], db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    """Updates settings for a namespace."""
    _check_settings_permission(db, user, namespace, "write")
    
    try:
        SettingsService.bulk_set(db, namespace, values, user_id=user.id)
        return ok(message=f"Settings for {namespace} updated successfully")
    except ValueError as e:
        return err(str(e))
    except Exception as e:
        return err(str(e))

@router.get("/{namespace}/schema")
def get_namespace_schema(namespace: str, db: Session = Depends(get_db), user: Any = Depends(get_current_user)):
    """Returns the configuration schema for a namespace."""
    _check_settings_permission(db, user, namespace, "read")
    
    schema = SettingsService.schema(namespace)
    return ok(schema)
