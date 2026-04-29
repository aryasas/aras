from arasCore.lib.core.base_model import ArasSoftModel, ArasModel, db


class CrmCustomer(ArasSoftModel):
    __tablename__ = "crm_customer"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_crm_customer_code"),
        db.Index("idx_crm_customer_name", "company_id", "name"),
    )

    company_id        = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    code              = db.Column(db.String(30), nullable=False)
    name              = db.Column(db.String(200), nullable=False)
    type              = db.Column(db.Enum("individual", "company"), default="individual", nullable=False)
    email             = db.Column(db.String(120), nullable=True)
    phone             = db.Column(db.String(50), nullable=True)
    mobile            = db.Column(db.String(50), nullable=True)
    address           = db.Column(db.Text, nullable=True)
    city              = db.Column(db.String(100), nullable=True)
    country           = db.Column(db.String(100), nullable=True)
    tax_id            = db.Column(db.String(50), nullable=True)
    currency_id       = db.Column(db.Integer, db.ForeignKey("currency.id"), nullable=True)
    credit_limit      = db.Column(db.Numeric(18, 4), default=0)
    payment_term_days = db.Column(db.Integer, default=30)
    salesperson_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    segment           = db.Column(db.String(50), nullable=True)
    tags              = db.Column(db.String(255), nullable=True)
    notes             = db.Column(db.Text, nullable=True)

    salesperson = db.relationship("User", foreign_keys=[salesperson_id])

    def __repr__(self):
        return f"<CrmCustomer {self.code} {self.name}>"


class CrmContact(ArasModel):
    __tablename__ = "crm_contact"

    customer_id = db.Column(db.Integer, db.ForeignKey("crm_customer.id"), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    title       = db.Column(db.String(100), nullable=True)
    email       = db.Column(db.String(120), nullable=True)
    phone       = db.Column(db.String(50), nullable=True)
    mobile      = db.Column(db.String(50), nullable=True)
    is_primary  = db.Column(db.Boolean, default=False)
    notes       = db.Column(db.Text, nullable=True)

    customer = db.relationship("CrmCustomer", backref=db.backref("contacts", lazy="dynamic"))

    def __repr__(self):
        return f"<CrmContact {self.name}>"
