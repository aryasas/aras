from datetime import date
from typing import Optional
from sqlalchemy import String, ForeignKey, Float, Date, Text, JSON, Boolean, Integer, event
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.base import ConfigBase, MasterDataBase, LineItemBase
from core import Aras

class Organization(ConfigBase):
    __tablename__ = "config_organizations"

    code: Mapped[str] = mapped_column(String(50), unique=True)
    profile: Mapped[str] = mapped_column(String(50), default="general")
    unit_type: Mapped[str] = mapped_column(String(50), default="organization")

    # Multi-company / group structure
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_organizations.id"), nullable=True)

    # Identity & Details
    legal_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trade_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    logo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Configuration
    base_currency_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_currencies.id"), nullable=True)
    fiscal_year_start_month: Mapped[int] = mapped_column(Integer, default=1)
    default_coa_template: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    default_charge_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_charges.id"), nullable=True)
    default_charge_enable: Mapped[bool] = mapped_column(Boolean, default=False)

    # Accounting mode
    enable_perpetual_inventory: Mapped[bool] = mapped_column(Boolean, default=False)
    enable_provisional_non_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    avg_cost_by_location: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_zero_stock: Mapped[bool] = mapped_column(Boolean, default=False)
    stock_valuation_method: Mapped[str] = mapped_column(String(10), default="FIFO", info={"choices": ["FIFO", "AVERAGE"]})

    # All default-account field names — used by inherit/fill actions
    _ACC_FIELDS = [
        "acc_bank_default_id", "acc_cash_default_id", "acc_receivable_default_id",
        "acc_payable_default_id", "acc_income_default_id", "acc_cogs_default_id",
        "acc_inventory_default_id", "acc_payroll_payable_id", "acc_payment_discount_id",
        "acc_write_off_id", "acc_unrealized_gain_loss_id", "acc_round_off_id",
        "acc_stock_received_not_billed_id", "acc_stock_provisional_id",
        "acc_stock_adjustment_id", "acc_expenses_in_valuation_id", "acc_stock_default_id",
        "acc_tax_output_ppn_id", "acc_tax_input_ppn_id",
    ]

    # fk_filter_fallback: use coa_source_org_id when set, otherwise own id
    _ACC_FK = {"fk_filter": {"org_id": "id"}, "fk_filter_fallback": {"org_id": "coa_source_org_id"}}
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

    # Stock / Inventory Accounts
    acc_stock_received_not_billed_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_provisional_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_adjustment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_expenses_in_valuation_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_stock_default_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)

    # Tax accounts
    acc_tax_output_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    acc_tax_input_ppn_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True, info=_ACC_FK)
    
    # Formatting Defaults
    date_format: Mapped[str] = mapped_column(String(20), default="DD/MM/YYYY")
    number_format: Mapped[str] = mapped_column(String(20), default="#,###.##")
    decimal_precision: Mapped[int] = mapped_column(Integer, default=2)

    # If set, account comboboxes use this org's COA instead of own (branch sharing parent ledger)
    coa_source_org_id: Mapped[Optional[int]] = mapped_column(ForeignKey("config_organizations.id"), nullable=True)

    # Relationships
    parent: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[parent_id], remote_side="Organization.id", backref="children")
    coa_source_org: Mapped[Optional["Organization"]] = relationship("Organization", foreign_keys=[coa_source_org_id])

    @Aras.model_action(name="mirror_coa", permission="edit", label="Mirror COA from Source", icon="Copy")
    def mirror_coa(self, db):
        from apps.accounting.models import Account
        source_org_id = self.coa_source_org_id or (self.parent_id if self.parent_id else None)
        if not source_org_id:
            from core.exceptions import ValidationException
            raise ValidationException("No COA source — set coa_source_org_id or parent_id first.")
        source_accounts = db.query(Account).filter_by(org_id=source_org_id).order_by(Account.id).all()
        if not source_accounts:
            from core.exceptions import ValidationException
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

    @Aras.model_action(name="inherit_accounts", permission="edit", label="Inherit from Parent", icon="ArrowDownToLine")
    def inherit_accounts(self, db):
        from apps.accounting.models import Account
        from core.exceptions import ValidationException
        if not self.parent_id:
            raise ValidationException("No parent — set parent_id first.")
        parent = db.get(Organization, self.parent_id)
        if not parent:
            raise ValidationException("Parent organization not found.")
        lookup_org_id = self.coa_source_org_id or self.id
        filled = skipped = 0
        for field in Organization._ACC_FIELDS:
            parent_acc_id = getattr(parent, field, None)
            if parent_acc_id is None:
                continue
            parent_acc = db.get(Account, parent_acc_id)
            if not parent_acc:
                continue
            own_acc = db.query(Account).filter_by(org_id=lookup_org_id, code=parent_acc.code).first()
            if own_acc:
                setattr(self, field, own_acc.id)
                filled += 1
            else:
                skipped += 1
        db.flush()
        return {"filled": filled, "skipped": skipped}

    @Aras.model_action(name="fill_default_accounts", permission="edit", label="Fill from Defaults", icon="Wand2")
    def fill_default_accounts(self, db):
        import json, os
        from apps.accounting.models import Account
        from core.exceptions import ValidationException
        config_path = os.path.join(os.path.dirname(__file__), "default_accounts.json")
        if not os.path.exists(config_path):
            raise ValidationException("default_accounts.json not found in config directory.")
        with open(config_path) as f:
            mapping: dict[str, str] = json.load(f)  # {field_name: account_code}
        filled = skipped = 0
        lookup_org_id = self.coa_source_org_id or self.id
        for field, code in mapping.items():
            if field not in Organization._ACC_FIELDS:
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
        if db is None:
            from sqlalchemy.orm import object_session
            db = object_session(self)
        if not db:
            return
        lookup_org_id = self.coa_source_org_id or self.id
        if not lookup_org_id:
            return
        for field in Organization._ACC_FIELDS:
            val = getattr(self, field, None)
            if val is None:
                continue
            acc = db.get(Account, val)
            if acc and acc.org_id != lookup_org_id:
                raise ValidationException(
                    f"Account '{acc.code}' (field: {field}) does not belong to the COA org (id={lookup_org_id})."
                )

# claude-sonnet-4-6
# after_insert fires after INSERT is flushed, so self.id is guaranteed to exist
@event.listens_for(Organization, "after_insert")
def _seed_reports_for_new_org(mapper, connection, target):
    from sqlalchemy.orm import object_session
    db = object_session(target)
    if db is None:
        return
    try:
        from apps.report.seed_reports import run_seed
        run_seed(db, target.id)
    except Exception:
        pass


class Currency(ConfigBase):
    __tablename__ = "config_currencies"
    code: Mapped[str] = mapped_column(String(10), unique=True)
    symbol: Mapped[str] = mapped_column(String(10))

class Uom(ConfigBase):
    __tablename__ = "config_uoms"

class PriceType(ConfigBase):
    __tablename__ = "config_price_types"
    kind: Mapped[str] = mapped_column(String(20), default="sales") # sales or purchase


class Charge(ConfigBase):
    __tablename__ = "config_charges"
    
    charge_type: Mapped[str] = mapped_column(String(20), default="Both", info={"choices": ["Sales", "Purchase", "Both"]})
    calc_method: Mapped[str] = mapped_column(String(10), default="Percent", info={"choices": ["Percent", "Fixed"]})
    rate: Mapped[float] = mapped_column(default=0)
    amount: Mapped[float] = mapped_column(default=0)
    is_inclusive: Mapped[bool] = mapped_column(default=False)
    is_compound: Mapped[bool] = mapped_column(default=False)
    sequence: Mapped[int] = mapped_column(default=10, info={"hidden": True})
    
    account_collected_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    account_paid_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)


class ExchangeRate(MasterDataBase):
    __tablename__ = "config_exchange_rates"

    currency_id: Mapped[int] = mapped_column(ForeignKey("config_currencies.id"))
    rate: Mapped[float] = mapped_column(Float)
    rate_date: Mapped[date] = mapped_column(Date)


class ModeOfPayment(MasterDataBase):
    __tablename__ = "config_payment_modes"
    
    payment_type: Mapped[str] = mapped_column(String(20), default="Cash", info={"choices": ["Cash", "Bank", "E-Wallet", "Other"]})
    
    accounts: Mapped[list["OrganizationPaymentAccount"]] = relationship("OrganizationPaymentAccount", back_populates="parent", cascade="all, delete-orphan")


class OrganizationPaymentAccount(LineItemBase):
    __tablename__ = "config_payment_accounts"
    __parent__ = "config_payment_modes"
    
    mode_id: Mapped[int] = mapped_column(ForeignKey("config_payment_modes.id"))
    account_id: Mapped[int] = mapped_column(ForeignKey("accounting_accounts.id"), info={"display_column": "display_name"})
    
    parent: Mapped["ModeOfPayment"] = relationship("ModeOfPayment", back_populates="accounts")


class PrintTemplate(MasterDataBase):
    __tablename__ = "config_print_templates"
    
    doc_type: Mapped[str] = mapped_column(String(50))
    code: Mapped[str] = mapped_column(String(50))
    engine: Mapped[str] = mapped_column(String(20), default="jinja")
    body_html: Mapped[str] = mapped_column(Text)
    header_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    footer_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    css: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(default=False)


class Notification(MasterDataBase):
    __tablename__ = "config_notifications"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("core_users.id"))
    type: Mapped[str] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(default=False)


class OrganizationVocabulary(ConfigBase):
    __tablename__ = "config_org_vocabulary"
    org_id: Mapped[int] = mapped_column(ForeignKey("config_organizations.id"))
    key: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))

class OrganizationPostingRule(ConfigBase):
    __tablename__ = "config_org_posting_rules"
    org_id: Mapped[int] = mapped_column(ForeignKey("config_organizations.id"))
    trx_type: Mapped[str] = mapped_column(String(50))
    debit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    credit_account_id: Mapped[Optional[int]] = mapped_column(ForeignKey("accounting_accounts.id"), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
