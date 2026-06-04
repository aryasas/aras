# claude-opus-4-8
"""Accounting-domain actions attached to the framework Organization model.

mirror_coa is an accounting concern (copies a chart of accounts) but operates on
the workspace Organization entity. Rather than couple core/workspace to accounting,
the action is defined here and monkey-attached at import time; we then re-run the
model's action discovery so the metadata/route layer picks it up.
"""
from core import Aras
from core.workspace.models import Organization


@Aras.model_action(name="mirror_coa", permission="edit", label="Mirror COA from Source", icon="Copy")
def mirror_coa(self, db):
    from apps.accounting.models import Account
    from core.exceptions import ValidationException
    source_org_id = self.coa_source_org_id or (self.parent_id if self.parent_id else None)
    if not source_org_id:
        raise ValidationException("No COA source — set coa_source_org_id or parent_id first.")
    source_accounts = db.query(Account).filter_by(org_id=source_org_id).order_by(Account.id).all()
    if not source_accounts:
        raise ValidationException(f"Source org {source_org_id} has no accounts to mirror.")
    existing_codes = {a.code for a in db.query(Account.code).filter_by(org_id=self.id).all()}
    # Map source id → new id for parent_id resolution
    id_map: dict[int, int] = {}
    for src in source_accounts:
        if src.code in existing_codes:
            continue
        new_acc = Account(
            org_id=self.id,
            code=src.code,
            name=src.name,
            account_type=src.account_type,
            is_group=src.is_group,
            parent_id=None,  # resolved below after flush
        )
        db.add(new_acc)
        db.flush()
        id_map[src.id] = new_acc.id
    # Wire parent_id using id_map
    for src in source_accounts:
        if src.parent_id and src.parent_id in id_map and src.id in id_map:
            child = db.get(Account, id_map[src.id])
            if child:
                child.parent_id = id_map[src.parent_id]
    db.flush()
    return {"mirrored": len(id_map), "skipped": len(existing_codes)}


# Attach to the framework model and refresh discovered actions.
Organization.mirror_coa = mirror_coa
Organization._discover_actions_and_computed_fields()
