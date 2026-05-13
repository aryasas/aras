from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, TYPE_CHECKING
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
