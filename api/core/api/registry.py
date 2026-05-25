from fastapi import APIRouter, Depends, Query
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Session
from ..lib.database import get_db
from ..logic.permissions import check_permissions, RBAC
from ..logic.ui_generator import UIGenerator
from ..auth.service import get_current_user_optional, require_admin
from ..auth.models import User

if TYPE_CHECKING:
    from ..aras import Aras

router = APIRouter(tags=["Registry Management"])

@router.get("/metadata/{resource_name:path}")
def get_resource_metadata(
    resource_name: str, 
    db: Session = Depends(get_db),
    lang: Optional[str] = Query(None),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Returns full UI metadata for a resource. Unauthenticated access allowed for UI rendering."""
    from ..base.model import Model
    from ..base.app import App
    
    # Normalize resource_name (ensure leading slash for matching)
    path = resource_name if resource_name.startswith("/") else f"/{resource_name}"
    path = path.replace("_", "-") # Ensure hyphens
    
    model_class = None
    
    # 1. Try to match by clean path
    for app_cls in App._registry.values():
        for model in app_cls.models:
            if hasattr(model, "__tablename__") and app_cls._get_clean_path(model.__tablename__) == path:
                model_class = model
                break
        if model_class: break
        
    # 2. Fallback to direct registry lookup (legacy/direct support)
    if not model_class:
        tablename = resource_name.split("/")[-1] if "/" in resource_name else resource_name
        model_class = Model._registry.get(tablename)
    
    # 3. Check core models
    if not model_class:
        from ..aras import Aras
        core_list = [
            Aras.User, Aras.Role, Aras.Permission, Aras.ActivityLog, Aras.ArasSetting,
            Aras.AppModel, Aras.ResourceModel, Aras.FieldModel, Aras.LinkModel, Aras.TranslationModel,
            Aras.WidgetModel, Aras.DashboardLayoutModel
        ]
        for m in core_list:
            if m.__tablename__ == tablename:
                model_class = m
                break
    
    if not model_class:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found in registry")

    # Determine if resource allows public metadata access
    is_public = getattr(model_class, "__public_read__", False)

    # If not public, we MUST have a user and they MUST have READ permission
    if not is_public:
        if not user:
            from fastapi import HTTPException
            raise HTTPException(status_code=401, detail="Authentication required for private metadata")
        
        if not user.is_admin and not RBAC.has_permission(db, user, model_class.__tablename__, "READ"):
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail=f"No READ permission on {model_class.__tablename__}")

    from ..base.view import View
    view_cls = View.get_for_model(model_class)
    if view_cls:
        return view_cls.render_metadata(db=db, lang=lang)
    return UIGenerator.generate_metadata(model_class, db=db, lang=lang)

@router.get("/models")
def get_registered_models(_ = Depends(require_admin)):
    """Returns all models currently in memory registry."""
    from ..base.model import Model
    return {name: str(cls) for name, cls in Model._registry.items()}

@router.get("/schemas")
def get_registered_schemas(_ = Depends(require_admin)):
    """Returns all schemas currently in memory registry."""
    from ..base.schema import Schema
    return {name: str(cls) for name, cls in Schema._registry.items()}

@router.get("/views")
def get_registered_views(_ = Depends(require_admin)):
    """Returns all views currently in memory registry."""
    from ..base.view import View
    return {name: str(cls) for name, cls in View._registry.items()}
