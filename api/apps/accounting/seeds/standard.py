# claude-opus-4-8
from core.config import AppConfigRegistry
from core.workspace.models import Currency, Organization

from apps.accounting.seed_coa import seed_coa
from apps.accounting.services.vocabulary import apply_profile_vocabulary


# claude-opus-4-8
def seed_trade_defaults(db):
    usd, _ = Currency.get_or_create(
        db,
        {"name": "US Dollar", "symbol": "$"},
        code="USD",
    )

    org = db.get(Organization, 1)
    if org is None:
        org = Organization(id=1, name="My Business", code="ORG1", is_default=True)
        db.add(org)
        db.flush()

    if not org.base_currency_id:
        org.base_currency_id = usd.id
    if not org.is_default:
        org.is_default = True
    if not org.legal_name:
        org.legal_name = org.name

    apply_profile_vocabulary(db, org.id, org.profile)

    slugs = seed_coa(db, org.id)
    cfg = AppConfigRegistry.get_or_create(db, "accounting", org.id)
    if cfg is None:
        raise ValueError("Accounting config model is not registered.")

    slug_to_field = {
        "bank": "acc_bank_default_id",
        "cash": "acc_cash_default_id",
        "receivable": "acc_receivable_default_id",
        "payable": "acc_payable_default_id",
        "revenue": "acc_income_default_id",
        "cogs": "acc_cogs_default_id",
        "inventory": "acc_inventory_default_id",
        "tax_output": "acc_tax_output_ppn_id",
    }
    for slug, field in slug_to_field.items():
        account = slugs.get(slug)
        if account is not None:
            setattr(cfg, field, account.id)

    # Organization identity (name/legal_name/currency) lives on the `org` row above —
    # single source of truth at /core-config/core-organizations. Instance-wide localization
    # defaults live in the `core` namespace (settings hub) — no config duplicate here.
    db.flush()


seed_trade_defaults.key = "trade_defaults"
seed_trade_defaults.label = "Trade Defaults"
seed_trade_defaults.optional = False
