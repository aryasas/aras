from sqlalchemy.orm import Session

from core.workspace.models import Organization

from ..org_presets import OrganizationVocabulary
from ..profiles import get_profile_labels


# claude-opus-4-8
def apply_profile_vocabulary(db: Session, org_id: int, profile: str) -> dict[str, str]:
    labels = get_profile_labels(profile)
    existing_rows = (
        db.query(OrganizationVocabulary)
        .filter(OrganizationVocabulary.org_id == org_id)
        .all()
    )
    existing_by_key = {row.key: row for row in existing_rows}

    for key, label in labels.items():
        row = existing_by_key.get(key)
        if row is None:
            db.add(OrganizationVocabulary(org_id=org_id, key=key, label=label, name=key))
        else:
            row.name = row.name or key
            row.label = label

    for key, row in existing_by_key.items():
        if key not in labels:
            db.delete(row)

    db.flush()
    return labels


# claude-opus-4-8
def resolve_labels(db: Session, org_id: int) -> dict[str, str]:
    org = db.get(Organization, org_id)
    if org is None:
        return get_profile_labels("general")

    labels = get_profile_labels(org.profile)
    rows = (
        db.query(OrganizationVocabulary)
        .filter(OrganizationVocabulary.org_id == org_id)
        .all()
    )
    for row in rows:
        labels[row.key] = row.label
    return labels
