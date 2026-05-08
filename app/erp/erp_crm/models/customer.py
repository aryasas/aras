from arasCore.arasgen import ArasGen
from app.erp.erp_crm.manifest import Crm
from arasCore.lib.core.base_model import ArasSoftModel, ArasModel, db


class CrmCustomer(ArasGen.Model, module=Crm):
    __title__     = "Customers"
    __icon__      = "fa-user-circle"
    __menu_order__= 2
    __tablename__ = "crm_customer"
    __table_args__ = (
        db.UniqueConstraint("company_id", "code", name="uq_crm_customer_code"),
        db.Index("idx_crm_customer_name", "company_id", "name"),
    )

    company_id        = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    code              = db.Column(db.String(30), nullable=False)
    name              = db.Column(db.String(200), nullable=False)
    group_id          = db.Column(db.Integer, db.ForeignKey("crm_customer_group.id"), nullable=True)
    email             = db.Column(db.String(120), nullable=True)
    phone             = db.Column(db.String(50), nullable=True)
    mobile            = db.Column(db.String(50), nullable=True)
    address           = db.Column(db.Text, nullable=True)
    city              = db.Column(db.String(100), nullable=True)
    country           = db.Column(db.String(100), nullable=True)
    tax_id            = db.Column(db.String(50), nullable=True)
    currency_id       = db.Column(db.Integer, db.ForeignKey("cfg_currency.id"), nullable=True)
    credit_limit      = db.Column(db.Numeric(18, 4), default=0)
    payment_term_days = db.Column(db.Integer, default=30)
    salesperson_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    segment           = db.Column(db.String(50), nullable=True)
    tags              = db.Column(db.String(255), nullable=True)
    notes             = db.Column(db.Text, nullable=True)

    salesperson = db.relationship("User", foreign_keys=[salesperson_id])

    def __repr__(self):
        return f"<CrmCustomer {self.code} {self.name}>"

    def detail_context(self, obj):
        if not obj:
            return {}
        try:
            from arasCore.lib.core.extensions import db
            rows = db.session.execute(db.text(
                "SELECT COALESCE(SUM(jl.debit),0) - COALESCE(SUM(jl.credit),0) "
                "FROM acc_journal_line jl "
                "JOIN acc_journal_entry je ON je.id = jl.entry_id "
                "WHERE jl.partner_id = :cid AND jl.partner_type = 'customer' "
                "  AND je.state = 'posted'"
            ), {"cid": obj.id}).fetchone()
            ar_balance = float(rows[0]) if rows and rows[0] else 0.0
            invoices = db.session.execute(db.text(
                "SELECT COUNT(*), COALESCE(SUM(total),0) "
                "FROM acc_sales_invoice WHERE customer_id = :cid AND state != 'cancelled'"
            ), {"cid": obj.id}).fetchone()
            return {"sidebar_cards": [{
                "title": "AR / Customer Balance",
                "rows": [
                    {"label": "Outstanding AR", "value": f"{ar_balance:,.2f}"},
                    {"label": "Total Invoices", "value": str(invoices[0] if invoices else 0)},
                    {"label": "Invoice Total", "value": f"{float(invoices[1] if invoices else 0):,.2f}"},
                ],
            }]}
        except Exception:
            return {}

class CrmContact(ArasGen.Model, module=Crm):
    __is_child__  = True
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
