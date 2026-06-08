# claude-opus-4-8
from core.config import AppConfigRegistry
from core.workspace.models import Organization
from plugins.commerce.models import ModeOfPayment, OrganizationPaymentAccount

from apps.accounting.models import Account


# claude-opus-4-8
def seed_trade_payment_accounts(db):
    org = db.get(Organization, 1)
    if org is None:
        return

    acc_cfg = AppConfigRegistry.get(db, "accounting", org.id)
    cash = db.get(Account, getattr(acc_cfg, "acc_cash_default_id", None)) if getattr(acc_cfg, "acc_cash_default_id", None) else None
    bank = db.get(Account, getattr(acc_cfg, "acc_bank_default_id", None)) if getattr(acc_cfg, "acc_bank_default_id", None) else None

    for name, payment_type, account in (
        ("Cash", "Cash", cash),
        ("Bank Transfer", "Bank", bank),
    ):
        mode, _ = ModeOfPayment.get_or_create(
            db,
            {"name": name, "payment_type": payment_type, "org_id": org.id},
            org_id=org.id,
            name=name,
        )
        if account is None:
            continue
        existing = db.query(OrganizationPaymentAccount).filter_by(mode_id=mode.id, account_id=account.id).first()
        if existing is None:
            db.add(OrganizationPaymentAccount(mode_id=mode.id, account_id=account.id))

    db.flush()


seed_trade_payment_accounts.key = "trade_payment_accounts"
seed_trade_payment_accounts.label = "Trade Payment Accounts"
seed_trade_payment_accounts.optional = False
