from fastapi import APIRouter, Depends
from typing import TYPE_CHECKING
from sqlalchemy.orm import Session
from ..lib.database import get_db
from ..logic.ui_generator import UIGenerator

if TYPE_CHECKING:
    from ..aras import Aras

router = APIRouter(tags=["Registry Management"])

@router.get("/metadata/{resource_name:path}")
async def get_resource_metadata(resource_name: str, db: Session = Depends(get_db)):
    """Returns full UI metadata for a resource, including DB overrides."""
    from ..base.model import Model
    
    # Resolve the actual table name (strip app prefix if present)
    tablename = resource_name.split("/")[-1] if "/" in resource_name else resource_name
    
    model_class = Model._registry.get(tablename)
    if not model_class:
        # Check if it's a core model (they might be registered by class name in main.py)
        from ..aras import Aras
        core_list = [
            Aras.User, Aras.Role, Aras.Permission, Aras.ActivityLog, Aras.ArasSetting,
            Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel, Aras.TranslationModel
        ]
        for m in core_list:
            if m.__tablename__ == tablename:
                model_class = m
                break
    
    if not model_class:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Resource '{tablename}' not found in registry")

    return UIGenerator.generate_metadata(model_class, db=db)

@router.get("/models")
async def get_registered_models():
    """Returns all models currently in memory registry."""
    from ..base.model import Model
    return {name: str(cls) for name, cls in Model._registry.items()}

@router.get("/schemas")
async def get_registered_schemas():
    """Returns all schemas currently in memory registry."""
    from ..base.schema import Schema
    return {name: str(cls) for name, cls in Schema._registry.items()}

@router.get("/views")
async def get_registered_views():
    """Returns all views currently in memory registry."""
    from ..base.view import View
    return {name: str(cls) for name, cls in View._registry.items()}
