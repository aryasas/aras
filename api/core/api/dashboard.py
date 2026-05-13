from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any, Optional, Dict
from pydantic import BaseModel

from ..lib.database import get_db
from ..registry.widget_model import WidgetModel
from ..registry.dashboard_layout_model import DashboardLayoutModel
from ..auth.service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

class DashboardLayoutCreate(BaseModel):
    name: str
    layout_config: Dict[str, Any] = {}
    is_default: bool = False

class DashboardLayoutUpdate(BaseModel):
    name: Optional[str] = None
    layout_config: Optional[Dict[str, Any]] = None
    is_default: Optional[bool] = None

@router.get("/layouts", response_model=List[dict])
async def get_dashboard_layouts(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Returns all dashboard layouts for the current user.
    """
    layouts = db.query(DashboardLayoutModel).filter(DashboardLayoutModel.user_id == user.id).all()
    return [layout.to_dict() for layout in layouts]

@router.get("/layouts/{layout_id}", response_model=dict)
async def get_dashboard_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Returns a specific dashboard layout by ID for the current user.
    """
    layout = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.id == layout_id,
        DashboardLayoutModel.user_id == user.id
    ).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")
    return layout.to_dict()

@router.post("/layouts", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dashboard_layout(
    layout_data: DashboardLayoutCreate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Creates a new dashboard layout for the current user.
    """
    new_layout = DashboardLayoutModel.create(
        db,
        {
            "name": layout_data.name,
            "user_id": user.id,
            "layout_config": layout_data.layout_config,
            "is_default": layout_data.is_default
        },
        user_id=user.id
    )
    if layout_data.is_default:
        # Ensure only one default dashboard per user
        db.query(DashboardLayoutModel).filter(
            DashboardLayoutModel.user_id == user.id,
            DashboardLayoutModel.id != new_layout.id
        ).update({"is_default": False})
        db.commit()
    return new_layout.to_dict()

@router.put("/layouts/{layout_id}", response_model=dict)
async def update_dashboard_layout(
    layout_id: int,
    layout_data: DashboardLayoutUpdate,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Updates an existing dashboard layout for the current user.
    """
    layout = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.id == layout_id,
        DashboardLayoutModel.user_id == user.id
    ).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")
    
    update_data = layout_data.dict(exclude_unset=True)
    if "is_default" in update_data and update_data["is_default"]:
        # Ensure only one default dashboard per user
        db.query(DashboardLayoutModel).filter(
            DashboardLayoutModel.user_id == user.id,
            DashboardLayoutModel.id != layout_id
        ).update({"is_default": False})
        db.commit()
    
    layout.update_self(db, update_data, user_id=user.id)
    return layout.to_dict()

@router.delete("/layouts/{layout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Deletes a dashboard layout for the current user.
    """
    layout = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.id == layout_id,
        DashboardLayoutModel.user_id == user.id
    ).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")
    
    layout.delete_self(db, user_id=user.id)
    return

@router.post("/layouts/{layout_id}/set-default", response_model=dict)
async def set_default_dashboard_layout(
    layout_id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Sets a specific dashboard layout as the default for the current user.
    """
    layout = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.id == layout_id,
        DashboardLayoutModel.user_id == user.id
    ).first()
    if not layout:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard layout not found")
    
    # Unset current default
    db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.user_id == user.id,
        DashboardLayoutModel.is_default == True
    ).update({"is_default": False})
    
    layout.update_self(db, {"is_default": True}, user_id=user.id)
    return layout.to_dict()

@router.get("/widgets", response_model=Dict[str, Any]) # Changed response_model to dict for layout
async def get_widgets(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Returns the current user's default dashboard layout, or system-defined widgets if no default is set.
    """
    # Try to find user's default layout
    default_layout = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.user_id == user.id,
        DashboardLayoutModel.is_default == True
    ).first()

    if default_layout:
        return {
            "layout_id": default_layout.id,
            "name": default_layout.name,
            "is_default": True,
            "layout_config": default_layout.layout_config
        }
    else:
        # Fallback to system-defined widgets
        system_widgets = WidgetModel.get_default_widgets(db)
        return {
            "name": "System Default Dashboard",
            "is_default": False,
            "layout_config": {
                "widgets": [w.to_dict() for w in system_widgets]
            }
        }
