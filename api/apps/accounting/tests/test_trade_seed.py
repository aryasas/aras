# claude-opus-4-8
from core.config import AppConfigRegistry
from core.manager.install_order import resolve_install_order
from core.seeds.base import run_app_seeds


# claude-opus-4-8
def test_standard_trade_seeds_create_working_org(db):
    from apps.accounting.models import Account
    from apps.party.models import Party
    from core.workspace.models import Organization

    for app_cls in resolve_install_order():
        run_app_seeds(app_cls, db)

    org = db.get(Organization, 1)
    assert org is not None
    assert org.base_currency_id is not None

    cfg = AppConfigRegistry.get(db, "accounting", org.id)
    assert cfg is not None
    assert cfg.acc_cash_default_id is not None
    assert cfg.acc_bank_default_id is not None
    assert cfg.acc_receivable_default_id is not None
    assert cfg.acc_payable_default_id is not None
    assert cfg.acc_income_default_id is not None
    assert cfg.acc_cogs_default_id is not None
    assert cfg.acc_inventory_default_id is not None

    default_accounts = (
        db.query(Account)
        .filter(Account.org_id == org.id, Account.code.in_(["11120", "11130", "11310", "21110", "41110", "51110", "11430", "21310"]))
        .all()
    )
    assert len(default_accounts) == 8

    assert db.query(Party).filter_by(org_id=org.id, name="Walk-in Customer").first() is not None
