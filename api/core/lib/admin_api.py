from fastapi import APIRouter, Depends, HTTPException, Body, UploadFile, File, Form
from typing import Optional
from sqlalchemy.orm import Session
from core import Aras
from core.lib.database import get_db
from .installer import AppInstaller
from .discovery import discover_apps

router = APIRouter(tags=["Framework Admin"])

@router.get("/apps")
async def get_apps_list(db: Session = Depends(get_db)):
    """
    List all discovered apps and their manifest details, merged with DB registry status.
    """
    from core.base.app import App
    from core.registry.app_model import AppModel
    
    discovered_apps = App._registry
    db_apps = {a.name: a for a in db.query(AppModel).all()}
    
    apps = []
    for app_name, app_cls in discovered_apps.items():
        manifest = app_cls.get_manifest()
        db_app = db_apps.get(app_name)
        
        manifest["is_active"] = db_app.is_active if db_app else True
        manifest["is_registered"] = db_app is not None
        apps.append(manifest)
        
    return apps

@router.post("/apps/install")
async def install_app(
    yaml_content: Optional[str] = Body(None, media_type="text/plain"),
    json_content: Optional[str] = Body(None, media_type="application/json"),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Installs a new app from YAML, JSON, or Python ZIP file.
    """
    try:
        app_path = None
        
        if yaml_content:
            app_path = AppInstaller.install_from_yaml(yaml_content)
        elif json_content:
            app_path = AppInstaller.install_from_json(json_content)
        elif file:
            content = await file.read()
            if file.filename.endswith(".zip"):
                app_path = AppInstaller.install_from_zip(content)
            elif file.filename.endswith(".yaml") or file.filename.endswith(".yml"):
                app_path = AppInstaller.install_from_yaml(content.decode("utf-8"))
            elif file.filename.endswith(".json"):
                app_path = AppInstaller.install_from_json(content.decode("utf-8"))
            else:
                raise ValueError("Unsupported file format. Use .zip, .yaml, or .json")
        else:
            raise ValueError("No installation content provided.")
        
        # Rediscover apps to include the new one
        discover_apps(package_path="apps")
        
        # Sync the new app to the registry
        Aras.Manager.Sync.sync_all(db)
        
        return {
            "status": "success",
            "message": f"App installed successfully at {app_path}",
            "path": app_path
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Installation failed: {str(e)}")
