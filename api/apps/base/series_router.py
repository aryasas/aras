from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from core.lib.numbering import numbering

router = APIRouter()

@router.get("/series/next")
def peek_series(
    key: str = Query(..., description="Series key (= model __tablename__)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org_id = getattr(current_user, "org_id", 0)
    next_number = numbering.peek(db, key, org_id=org_id)
    return {"next": next_number}
