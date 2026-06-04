# claude-opus-4-8
from core.workspace.models import Organization

from apps.party.models import Party
from apps.accounting.services.vocabulary import apply_profile_vocabulary


# claude-opus-4-8
def seed_trade_parties(db):
    org = db.get(Organization, 1)
    if org is None:
        org = Organization(id=1, name="My Business", code="ORG1", is_default=True)
        db.add(org)
        db.flush()

    apply_profile_vocabulary(db, org.id, org.profile)

    Party.get_or_create(
        db,
        {"role": "customer", "role_label": "Customer"},
        org_id=org.id,
        name="Walk-in Customer",
    )
    Party.get_or_create(
        db,
        {"role": "supplier", "role_label": "Supplier"},
        org_id=org.id,
        name="General Supplier",
    )
    db.flush()


seed_trade_parties.key = "trade_parties"
seed_trade_parties.label = "Trade Parties"
seed_trade_parties.optional = False
