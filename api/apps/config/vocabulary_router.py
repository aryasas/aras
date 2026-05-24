from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from .models import OrganizationVocabulary

vocabulary_router = APIRouter()


class VocabularyItem(BaseModel):
    key: str
    label: str

    class Config:
        from_attributes = True


@vocabulary_router.get("/organizations/{org_id}/vocabulary", response_model=List[VocabularyItem])
def get_org_vocabulary(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(OrganizationVocabulary).filter(OrganizationVocabulary.org_id == org_id).all()


@vocabulary_router.put("/organizations/{org_id}/vocabulary")
def set_org_vocabulary(
    org_id: int,
    items: List[VocabularyItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(OrganizationVocabulary).filter(OrganizationVocabulary.org_id == org_id).delete()
    for item in items:
        db.add(OrganizationVocabulary(org_id=org_id, key=item.key, label=item.label))
    db.commit()
    return {"ok": True}
