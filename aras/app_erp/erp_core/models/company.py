from arasCore.lib.base_model import ArasModel, db


class Company(ArasModel):
    __tablename__ = "company"
    __display_fields__ = ("code", "legal_name")

    # Identity
    code                    = db.Column(db.String(20), unique=True, nullable=False)
    legal_name              = db.Column(db.String(255), nullable=False)
    trade_name              = db.Column(db.String(255), nullable=True)
    tax_id                  = db.Column(db.String(50), nullable=True)
    address                 = db.Column(db.Text, nullable=True)
    phone                   = db.Column(db.String(50), nullable=True)
    email                   = db.Column(db.String(120), nullable=True)
    website                 = db.Column(db.String(255), nullable=True)
    logo_path               = db.Column(db.String(500), nullable=True)
    base_currency_id        = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=True)
    fiscal_year_start_month = db.Column(db.SmallInteger, default=1)
    default_charge_id       = db.Column(db.Integer, db.ForeignKey("charge.id"), nullable=True)
    default_coa_template    = db.Column(db.String(50), nullable=True)

    # Multi-company / group structure
    parent_id               = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=True)
    is_group                = db.Column(db.Boolean, default=False, nullable=False)

    parent   = db.relationship("Company", remote_side="Company.id", foreign_keys=[parent_id],
                               backref=db.backref("children", lazy="dynamic"), overlaps="children")

    # Accounting mode
    enable_perpetual_inventory       = db.Column(db.Boolean, default=False, nullable=False)
    enable_provisional_non_stock     = db.Column(db.Boolean, default=False, nullable=False)

    # Default Accounts
    acc_bank_default_id              = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_cash_default_id              = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_receivable_default_id        = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_payable_default_id           = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_income_default_id            = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_cogs_default_id              = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_payroll_payable_id           = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_payment_discount_id          = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_write_off_id                 = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_unrealized_gain_loss_id      = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_round_off_id                 = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    # Stock / Inventory Accounts (perpetual)
    acc_inventory_default_id         = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_stock_received_not_billed_id = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_stock_provisional_id         = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_stock_adjustment_id          = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)
    acc_expenses_in_valuation_id     = db.Column(db.BigInteger, db.ForeignKey("acc_account.id"), nullable=True)

    def __repr__(self):
        return f"<Company {self.code}>"
