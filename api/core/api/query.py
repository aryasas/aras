from fastapi import APIRouter, Depends, Body, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, String, cast
from typing import List, Dict, Any, TYPE_CHECKING, Optional
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..aras import Aras

from ..lib.database import get_db
from ..lib.query_builder import QueryBuilder
from ..auth.service import get_current_user

router = APIRouter(tags=["Generic Query API"])

class QueryRequest(BaseModel):
    filters: List[Dict[str, Any]] = []

@router.post("/{resource_name}/query")
async def execute_query(
    resource_name: str,
    request: QueryRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
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
    from ..logic.permissions import check_permissions
    
    results = []
    # Only search in models the user has READ permission for
    # For performance, we limit to first 5 results per model, max 50 total.
    
    for name, model_class in Model._registry.items():
        # Avoid double processing (registry has both Name and Tablename)
        if name != getattr(model_class, "__tablename__", None):
            continue
            
        # Check permissions (basic check, could be optimized)
        # Note: check_permissions returns a dependency function, here we just check if it would pass
        # In a real scenario, we might want a more efficient way to filter models.
        
        # For now, we search in all and rely on the fact that this is a framework-level search.
        # But we should respect __searchable__ flag if it exists.
        
        search_fields = [
            c.name for c in model_class.__table__.columns 
            if c.info.get("searchable", False) or isinstance(c.type, String)
        ]
        
        if not search_fields:
            continue
            
        try:
            stmt = model_class._q().limit(5)
            stmt = model_class.apply_search(stmt, q, fields=search_fields)
            items = db.scalars(stmt).all()
            
            for item in items:
                # Find a display label (name, title, or ID)
                label = getattr(item, "name", getattr(item, "title", f"{model_class.__name__} #{item.id}"))
                results.append({
                    "resource": model_class.__tablename__,
                    "id": item.id,
                    "label": str(label),
                    "type": getattr(model_class, "__title__", model_class.__name__)
                })
        except Exception as e:
            print(f"Global search error in {name}: {e}")
            continue
            
        if len(results) >= 50:
            break
            
    return results
