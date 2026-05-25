from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Any
from sqlalchemy.orm import Session

from ..lib.database import get_db
from ..auth.service import require_admin, get_current_user
from ..logic.installer import AppInstaller
from ..logic.discovery import discover_apps

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
