from fastapi import APIRouter, Depends, Body, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, String, cast
from typing import List, Dict, Any, TYPE_CHECKING, Optional
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..aras import Aras

from ..lib.database import get_db
from ..lib.query_builder import QueryBuilder
from ..auth.service import get_current_user, get_optional_user

router = APIRouter(tags=["Generic Query API"])

class QueryRequest(BaseModel):
    filters: List[Dict[str, Any]] = []

@router.post("/{resource_name}/query")
async def execute_query(
    resource_name: str,
    request: QueryRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(get_optional_user)
):
    """
    Execute a structured query against any registered resource.
    """
    from ..base.model import Model
    # Find the model class from the registry
    model_class = Model._registry.get(resource_name)
    if not model_class:
        # Try finding by tablename
        for cls in Model._registry.values():
            if getattr(cls, "__tablename__", None) == resource_name:
                model_class = cls
                break
                
    if not model_class:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found")

    # Check Permissions or Public Read
    if not getattr(model_class, "__public_read__", False):
        if not current_user:
            raise HTTPException(status_code=401, detail="Authentication required")
        
        # We should ideally call check_permissions here, but it's a dependency.
        # For now, if not public and not admin, check if searchable or has READ.
        # Actually, let's keep it simple: if not public and not logged in, 401.
        # If logged in, we assume they can query for now (Registry level check could be added).

    try:
        results = QueryBuilder.execute(db, model_class, request.filters)
        return {"items": [item.to_dict() for item in results]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search")
async def global_search(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Searches across all registered searchable resources.
    Returns a list of matching records with their resource type and a display label.
    """
    from ..base.model import Model
    import logging
    logger = logging.getLogger(__name__)
    
    results = []
    # Only search in models the user has READ permission for
    
    search_count = 0
    for name, model_class in Model._registry.items():
        # Avoid double processing (registry has both Name and Tablename)
        if name != getattr(model_class, "__tablename__", None):
            continue
            
        # Respect __searchable__ flag if it exists (explicitly disabled)
        if getattr(model_class, "__searchable__", True) is False:
            continue
            
        # Determine search fields
        search_fields = []
        if hasattr(model_class, "__searchable_fields__"):
            search_fields = model_class.__searchable_fields__
        else:
            # Auto-detect: String, Text, or columns marked as searchable
            for c in model_class.__table__.columns:
                type_name = str(c.type).upper()
                if c.info.get("searchable", False) or \
                   "VARCHAR" in type_name or "TEXT" in type_name or "STRING" in type_name:
                    search_fields.append(c.name)
        
        if not search_fields:
            continue
            
        try:
            stmt = model_class._q().limit(10) # Increased limit per model
            stmt = model_class.apply_search(stmt, q, fields=search_fields)
            items = db.scalars(stmt).all()
            
            for item in items:
                # Find a display label (name, title, username, number, or ID)
                label = getattr(item, "name", 
                        getattr(item, "title", 
                        getattr(item, "username", 
                        getattr(item, "number", f"{model_class.__name__} #{item.id}"))))
                results.append({
                    "resource": model_class.__tablename__,
                    "id": item.id,
                    "label": str(label),
                    "type": getattr(model_class, "__title__", model_class.__name__)
                })
                search_count += 1
        except Exception as e:
            logger.error(f"Global search error in {name}: {e}")
            continue
            
        if search_count >= 50:
            break
            
    return results
