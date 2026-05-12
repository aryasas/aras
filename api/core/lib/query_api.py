"""
Purpose: Standardized interface for executing advanced JSON-driven queries.
Context: Level 3 API. Exposes the QueryBuilder logic to the frontend.
Impact: Enables generic reporting and analytics without writing new endpoints.
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..base.aras import Aras
from ..lib.database import get_db
from ..lib.query_builder import QueryBuilder
from ..auth.service import get_current_user

router = APIRouter(prefix="/query", tags=["BI & Reporting"])

@router.post("/{resource_name}")
async def execute_query(
    resource_name: str,
    filters: List[Dict[str, Any]] = Body(...),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Executes a dynamic query on a resource.
    Body format: [{"field": "price", "op": ">", "value": 100}]
    """
    # Find the model class from the registry
    registry = Aras.get_registered("Model")
    model_class = None
    for name, cls in registry.items():
        if getattr(cls, "__tablename__", None) == resource_name:
            model_class = cls
            break
            
    if not model_class:
        return {"error": "Resource not found"}, 404
        
    results = QueryBuilder.execute(db, model_class, filters)
    return [row.to_dict() for row in results]
