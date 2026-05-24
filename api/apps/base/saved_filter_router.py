import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from .saved_filter import SavedFilter


class SavedFilterCreate(BaseModel):
    resource: str = Field(..., max_length=100)
    name: str = Field(..., max_length=100)
    filters_json: str
    is_default: bool = False


class SavedFilterResponse(BaseModel):
    id: int
    resource: str
    name: str
    filters_json: str
    is_default: bool
    org_id: int

    class Config:
        from_attributes = True


router = APIRouter()


@router.get("/sys_filters")
def list_saved_filters(
    filters: Optional[str] = None,
    resource: Optional[str] = None,
    request: Request = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(SavedFilter).filter(SavedFilter.org_id == request.state.org_id)

    # frontend sends: filters=[{"field":"resource","op":"=","value":"..."}]
    if filters:
        try:
            for f in json.loads(filters):
                if f.get("field") == "resource":
                    q = q.filter(SavedFilter.resource == f["value"])
        except (json.JSONDecodeError, KeyError):
            pass
    elif resource:
        q = q.filter(SavedFilter.resource == resource)

    items = q.all()
    return {"items": [SavedFilterResponse.model_validate(i) for i in items], "total": len(items)}


@router.post("/sys_filters", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    filter_data: SavedFilterCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if filter_data.is_default:
        existing = db.query(SavedFilter).filter(
            SavedFilter.resource == filter_data.resource,
            SavedFilter.org_id == request.state.org_id,
            SavedFilter.is_default == True,
        ).first()
        if existing:
            existing.is_default = False
            db.add(existing)

    new_filter = SavedFilter(
        resource=filter_data.resource,
        name=filter_data.name,
        filters_json=filter_data.filters_json,
        is_default=filter_data.is_default,
        org_id=request.state.org_id,
    )
    db.add(new_filter)
    db.commit()
    db.refresh(new_filter)
    return new_filter


@router.delete("/sys_filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    filter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    f = db.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.org_id == request.state.org_id,
    ).first()
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")
    db.delete(f)
    db.commit()
