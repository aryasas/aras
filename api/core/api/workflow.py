from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any

from ..lib.database import get_db
from ..auth.service import get_current_user

router = APIRouter(tags=["Workflow API"])


@router.get("/handlers")
async def list_handlers(_: Any = Depends(get_current_user)):
    """Returns all registered workflow handler names and descriptions."""
    from ..logic.handler_registry import HandlerRegistry
    return HandlerRegistry.list_handlers()


@router.get("/{resource_name}/{item_id}/actions")
async def get_actions(
    resource_name: str,
    item_id: int,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    from ..base.model import Model
    from ..manager.workflow_manager import WorkflowManager

    model_class = Model._registry.get(resource_name)
    if not model_class:
        raise HTTPException(status_code=404, detail="Resource not found")

    item = db.get(model_class, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return WorkflowManager.get_available_actions(item, current_user, db=db)


@router.post("/{resource_name}/{item_id}/action/{action_name}")
async def trigger_action(
    resource_name: str,
    item_id: int,
    action_name: str,
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    from ..base.model import Model
    from ..manager.workflow_manager import WorkflowManager

    model_class = Model._registry.get(resource_name)
    if not model_class:
        raise HTTPException(status_code=404, detail="Resource not found")

    item = db.get(model_class, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    try:
        WorkflowManager.trigger_action(db, item, action_name, current_user)
        db.commit()
        return {
            "status": "success",
            "message": f"Action '{action_name}' executed successfully",
            "new_status": item.status
        }
    except (ValueError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Workflow error: {str(e)}")
