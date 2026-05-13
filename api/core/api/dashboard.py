from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Any
from ..lib.database import get_db
from ..registry.widget_model import WidgetModel
from ..auth.service import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/widgets", response_model=List[dict])
async def get_widgets(
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user)
):
    """
    Returns configured dashboard widgets for the current user.
    """
    widgets = WidgetModel.get_default_widgets(db)
    # Convert to dict for response
    return [w.to_dict() for w in widgets]
