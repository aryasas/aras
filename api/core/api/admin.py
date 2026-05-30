from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Any
from sqlalchemy.orm import Session

from ..lib.database import get_db
from ..auth.service import require_admin, get_current_user
from ..logic.installer import AppInstaller
from ..logic.discovery import discover_apps
from ..lib.helpers import to_label_case

router = APIRouter(tags=["Framework Admin"])


@router.get("/apps")
def get_apps_list(db: Session = Depends(get_db), _: Any = Depends(require_admin)):
    """List all discovered apps and their manifest details, merged with DB registry status."""
    from ..base.app import App
    from ..registry.app_model import AppModel

    discover_apps()
    registry_apps = {app.name: app for app in db.query(AppModel).all()}

    results = []
    for app_cls in App._registry.values():
        manifest = app_cls.get_manifest()
        # Framework apps (e.g. config/settings, dev) are part of the platform,
        # not installable extensions — hide from App Manager.
        if manifest.get("app_type") == "framework":
            continue
        db_record = registry_apps.get(manifest["name"])

        results.append({
            **manifest,
            "is_installed": db_record is not None,
            "is_active": db_record.is_active if db_record else False,
            "is_registered": db_record is not None,
            "is_sub_module": bool(manifest.get("parent_name")),
        })

    return results


@router.post("/install")
def install_app(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Installs a new app from YAML, JSON, or Python ZIP file."""
    content = file.file.read()
    filename = file.filename

    try:
        if filename.endswith(".zip"):
            AppInstaller.install_from_zip(content, db)
        elif filename.endswith(".yaml") or filename.endswith(".yml"):
            AppInstaller.install_from_yaml(content.decode(), db)
        elif filename.endswith(".json"):
            AppInstaller.install_from_json(content.decode(), db)
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        return {"status": "success", "message": "App installed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/uninstall/{app_name}")
def uninstall_app(
    app_name: str,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Uninstalls an app, removes its directory, and purges registry records."""
    try:
        AppInstaller.uninstall_app(app_name, db)
        return {"status": "success", "message": f"App {app_name} uninstalled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/apps/capabilities")
def get_app_capabilities(db: Session = Depends(get_db), _: Any = Depends(get_current_user)):
    """Returns active app names and the merged optional_features map for all active apps.
    Used by the UI to conditionally show/hide feature toggles in Organization config.
    """
    from ..registry.app_model import AppModel
    active_apps = db.query(AppModel).filter(AppModel.is_active == True).all()
    active_app_names = [a.name for a in active_apps]
    optional_features: dict = {}
    for app in active_apps:
        optional_features.update(app.optional_features or {})
    return {
        "active_apps": active_app_names,
        "optional_features": optional_features,
    }


@router.get("/quick-actions")
def get_quick_actions(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """Returns a list of all searchable actions, resources, and routes for the current user."""
    from ..base.model import Model
    from ..logic.permissions import RBAC
    from ..auth.models import UserPreference
    from ..base.app import App
    import json

    actions = []

    # 1. Resources & Model Actions (RBAC filtered)
    if user.is_admin:
        readable_resources = set(Model._registry.keys())
    else:
        readable_resources = RBAC.get_readable_resources(db, user)

    # Map models to apps for better labeling
    model_to_app = {}
    for app_name, app_cls in App._registry.items():
        for m in app_cls.models:
            model_to_app[m.__tablename__] = app_name

    for res_name in readable_resources:
        model_cls = Model._registry.get(res_name)
        if not model_cls:
            continue
        
        app_name = model_to_app.get(res_name, "core")
        
        # Add Resource itself
        actions.append({
            "id": f"res:{res_name}",
            "label": getattr(model_cls, "__title__", to_label_case(res_name)),
            "kind": "resource",
            "target": res_name,
            "icon": "Database",
            "app": app_name
        })

        # Add Model Actions
        for act_name, model_action in model_cls._actions.items():
            perm = model_action.permission or "edit"
            # Normalize permission to RBAC action
            rbac_action = "UPDATE" if perm in ["edit", "update", "write"] else perm.upper()
            
            if user.is_admin or RBAC.has_permission(db, user, res_name, rbac_action):
                actions.append({
                    "id": f"act:{res_name}:{act_name}",
                    "label": f"{model_action.label or act_name.title()} ({res_name})",
                    "kind": "action",
                    "target": f"{res_name}:{act_name}",
                    "icon": model_action.icon or "Play",
                    "app": app_name
                })

    # 2. Standard Routes
    standard_routes = [
        {"label": "Dashboard", "target": "/dashboard", "icon": "LayoutDashboard"},
        {"label": "Settings", "target": "/settings", "icon": "Settings"},
        {"label": "User Profile", "target": "/profile", "icon": "User"},
    ]
    for r in standard_routes:
        actions.append({
            "id": f"route:{r['target']}",
            "label": r["label"],
            "kind": "route",
            "target": r["target"],
            "icon": r["icon"],
            "app": "core"
        })

    # 3. Add History items if they exist (could be used by frontend for sorting)
    history_pref = db.query(UserPreference).filter(
        UserPreference.user_id == user.id,
        UserPreference.key == "history:resources"
    ).first()
    if history_pref and history_pref.value:
        try:
            history = json.loads(history_pref.value)
            # Tag history items
            for h_res in history:
                for act in actions:
                    if act["id"] == f"res:{h_res}":
                        act["recent"] = True
        except:
            pass

    return actions
