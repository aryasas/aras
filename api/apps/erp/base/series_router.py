from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from core.manager.naming_manager import SeriesManager

router = APIRouter()

@router.get("/series/next")
def peek_series(
    key: str = Query(..., description="Series key (= model __tablename__)"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    next_number = SeriesManager.peek_next(db, key)
    return {"next": next_number}
