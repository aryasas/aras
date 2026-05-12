"""
Purpose: Standardized interface for executing a state transition.
Context: Level 3 API. Exposes the WorkflowManager logic to the frontend.
Impact: Enables generic document lifecycle management.
"""
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from ..aras import Aras
from ..lib.database import get_db
from ..auth.service import get_current_user

router = APIRouter(prefix="/workflow", tags=["Workflow Engine"])

@router.post("/{resource_name}/{item_id}/transition")
async def transition_document(
    resource_name: str,
    item_id: int,
    data: Dict[str, str] = Body(..., example={"state": "Submitted"}),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Moves a document to a new state.
    """
    target_state = data.get("state")
    
    # 1. Find Model
    registry = Aras.get_registered("Model")
    model_class = None
    for name, cls in registry.items():
        if getattr(cls, "__tablename__", None) == resource_name:
            model_class = cls
            break
            
    if not model_class:
        raise HTTPException(status_code=404, detail="Resource not found")
        
    # 2. Find Item
    item = model_class.get(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    # 3. Execute Transition
    success, message = Aras.Manager.Workflow.transition(db, item, target_state, user)
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
        
    return {"status": "success", "message": message, "new_state": item.status}
