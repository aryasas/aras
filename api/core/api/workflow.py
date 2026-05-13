from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..aras import Aras
    
from ..lib.database import get_db
from ..auth.service import get_current_user

router = APIRouter(tags=["Workflow API"])

@router.post("/{resource_name}/{item_id}/action/{action_name}")
async def trigger_action(
    resource_name: str,
    item_id: int,
    action_name: str,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """
    Trigger a workflow action on a specific resource item.
    """
    from ..base.model import Model
    model_class = Model._registry.get(resource_name)
    if not model_class:
        raise HTTPException(status_code=404, detail="Resource not found")

    item = db.get(model_class, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # TODO: Implement actual workflow engine invocation
    return {
        "status": "success",
        "message": f"Action '{action_name}' triggered on {resource_name}:{item_id}",
        "action": action_name,
        "item": item_id
    }
