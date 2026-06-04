from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from core.lib.database import get_db
from core.auth.service import get_current_user
from core.auth.models import User
from core.workspace.models import Organization
from .org_presets import OrganizationVocabulary
from .profiles import PROFILE_DEFAULTS, get_profile_catalog
from .services.vocabulary import apply_profile_vocabulary, resolve_labels

vocabulary_router = APIRouter()


class VocabularyItem(BaseModel):
    key: str
    label: str

    class Config:
        from_attributes = True


# claude-opus-4-8
class ProfileCatalogItem(BaseModel):
    key: str
    display_name: str
    description: str
    labels: dict[str, str]


# claude-opus-4-8
class ProfileUpdatePayload(BaseModel):
    profile: str


# claude-opus-4-8
def _labels_to_items(labels: dict[str, str]) -> list[VocabularyItem]:
    return [VocabularyItem(key=key, label=label) for key, label in labels.items()]


# claude-opus-4-8
@vocabulary_router.get("/vocabulary/profiles", response_model=List[ProfileCatalogItem])
def get_vocabulary_profiles(
    current_user: User = Depends(get_current_user),
):
    return get_profile_catalog()


# claude-opus-4-8
@vocabulary_router.get("/organizations/{org_id}/vocabulary", response_model=List[VocabularyItem])
def get_org_vocabulary(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _labels_to_items(resolve_labels(db, org_id))


# claude-opus-4-8
@vocabulary_router.put("/organizations/{org_id}/profile")
def set_org_profile(
    org_id: int,
    payload: ProfileUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organization not found")
    if payload.profile not in PROFILE_DEFAULTS:
        raise HTTPException(status_code=400, detail="Unknown organization profile")

    org.profile = payload.profile
    labels = apply_profile_vocabulary(db, org_id, payload.profile)
    db.commit()
    return {"profile": org.profile, "labels": labels}


@vocabulary_router.put("/organizations/{org_id}/vocabulary")
def set_org_vocabulary(
    org_id: int,
    items: List[VocabularyItem],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(OrganizationVocabulary).filter(OrganizationVocabulary.org_id == org_id).delete()
    for item in items:
        db.add(OrganizationVocabulary(org_id=org_id, key=item.key, label=item.label, name=item.key))
    db.commit()
    return {"ok": True}
