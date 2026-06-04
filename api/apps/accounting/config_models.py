# claude-sonnet-4-6
"""
AccountingConfig — per-organization accounting defaults, owned by the accounting app.

These were historically 14 acc_* FK columns bolted onto Organization, which forced
the framework/config layer to depend on accounting. Moving them here (registered via
App.config_model) lets the framework read them by key only when accounting is
installed — a free plan simply has no AccountingConfig row, no coupling.
"""
from typing import Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core.config import AppConfig

# fk filter so account comboboxes scope to the config's org (or its COA source)
_ACC_FK = {"fk_filter": {"org_id": "org_id"}}


class AccountingConfig(AppConfig):
    __tablename__ = "accounting_config"
    __config_for__ = "accounting"

    # All default-account field names — used by inherit/fill actions (moved from Organization)
    _ACC_FIELDS = [
        "acc_bank_default_id", "acc_cash_default_id", "acc_receivable_default_id",
        "acc_payable_default_id", "acc_income_default_id", "acc_cogs_default_id",
        "acc_inventory_default_id", "acc_payroll_payable_id", "acc_payment_discount_id",
        "acc_write_off_id", "acc_unrealized_gain_loss_id", "acc_round_off_id",
        "acc_tax_output_ppn_id", "acc_tax_input_ppn_id",
    ]

    default_coa_template: Mapped[Optional[str]] = mapped_column(nullable=True)
    default_charge_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_charges.id"), nullable=True)
    default_charge_enable: Mapped[bool] = mapped_column(default=False)

    acc_bank_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_cash_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_receivable_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_payable_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_income_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_cogs_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_inventory_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_payroll_payable_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_payment_discount_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_write_off_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_unrealized_gain_loss_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_round_off_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_tax_output_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_tax_input_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)

    def _coa_lookup_org(self, db):
        """COA source org: this config's org, or its coa_source_org_id if branch-shares a ledger."""
        from core.workspace.models import Organization
        org = db.get(Organization, self.org_id)
        return (org.coa_source_org_id if org and org.coa_source_org_id else self.org_id)

    from core import Aras

    @Aras.model_action(name="fill_default_accounts", permission="edit", label="Fill from Defaults", icon="Wand2")
    def fill_default_accounts(self, db):
        import json, os
        from apps.accounting.models import Account
        from core.exceptions import ValidationException
        config_path = os.path.join(os.path.dirname(__file__), "default_accounts.json")
        if not os.path.exists(config_path):
            raise ValidationException("default_accounts.json not found.")
        with open(config_path) as f:
            mapping = json.load(f)
        filled = skipped = 0
        lookup_org_id = self._coa_lookup_org(db)
        for field, code in mapping.items():
            if field not in self._ACC_FIELDS:
                continue
            acc = db.query(Account).filter_by(org_id=lookup_org_id, code=code).first()
            if acc:
                setattr(self, field, acc.id)
                filled += 1
            else:
                skipped += 1
        db.flush()
        return {"filled": filled, "skipped": skipped}

    def before_save(self, is_new: bool, db=None):
        from apps.accounting.models import Account
        from core.exceptions import ValidationException
        db = db or self.db_session
        if not db:
            return
        lookup_org_id = self._coa_lookup_org(db)
        for field in self._ACC_FIELDS:
            val = getattr(self, field, None)
            if val is None:
                continue
            acc = db.get(Account, val)
            if acc and acc.org_id != lookup_org_id:
                raise ValidationException(
                    f"Account '{acc.code}' (field: {field}) does not belong to the COA org (id={lookup_org_id})."
                )
