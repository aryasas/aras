from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from sqlalchemy import func

from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from .saved_filter import SavedFilter
# Pydantic models for request/response
from pydantic import BaseModel, Field

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
    org_id: int # Assuming org_id is part of MasterDataBase

    class Config:
        from_attributes = True # Allow ORM models to be converted to Pydantic

router = APIRouter()

@router.get("/saved-filters", response_model=List[SavedFilterResponse])
def list_saved_filters(resource: str, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    List saved filters for a given resource and the current organization.
    """
    filters = db.query(SavedFilter).filter(
        SavedFilter.resource == resource,
        SavedFilter.org_id == request.state.org_id
    ).all()
    return filters

@router.post("/saved-filters", response_model=SavedFilterResponse, status_code=status.HTTP_201_CREATED)
def create_saved_filter(
    filter_data: SavedFilterCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new saved filter.
    """
    # Check if a default filter already exists for this resource and user, and if new one is default
    if filter_data.is_default:
        existing_default = db.query(SavedFilter).filter(
            SavedFilter.resource == filter_data.resource,
            SavedFilter.org_id == request.state.org_id,
            SavedFilter.is_default == True
        ).first()
        if existing_default:
            existing_default.is_default = False # Unset existing default
            db.add(existing_default)

    new_filter = SavedFilter(
        resource=filter_data.resource,
        name=filter_data.name,
        filters_json=filter_data.filters_json,
        is_default=filter_data.is_default,
        org_id=request.state.org_id
    )
    db.add(new_filter)
    db.commit()
    db.refresh(new_filter)
    return new_filter

@router.delete("/saved-filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_filter(
    filter_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a saved filter by ID.
    """
    filter_to_delete = db.query(SavedFilter).filter(
        SavedFilter.id == filter_id,
        SavedFilter.org_id == request.state.org_id
    ).first()

    if not filter_to_delete:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved filter not found")

    db.delete(filter_to_delete)
    db.commit()
    return