"""Seed core data: default company, IDR currency, SUPERADMIN role, sequences."""
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.company import CoreCompany
from aras.app_erp.erp_core.models.currency import CoreCurrency
from aras.app_erp.erp_core.models.acl import CoreRole, CorePermission
from aras.app_erp.erp_core.models.sequence import CoreSequence
from aras.app_erp.erp_core.models.setting import CoreSetting


SEQUENCES = [
    ("sales.order",            "SO",   5, "yearly"),
    ("sales.invoice",          "INV",  5, "yearly"),
    ("sales.payment",          "RCV",  5, "yearly"),
    ("sales.credit_note",      "CN",   5, "yearly"),
    ("purchase.order",         "PO",   5, "yearly"),
    ("purchase.bill",          "BILL", 5, "yearly"),
    ("purchase.payment",       "PAY",  5, "yearly"),
    ("inventory.transfer",     "TRF",  5, "yearly"),
    ("inventory.adjustment",   "ADJ",  5, "yearly"),
    ("inventory.grn",          "GRN",  5, "yearly"),
    ("accounting.journal",     "JV",   5, "yearly"),
    ("accounting.payment",     "PMT",  5, "yearly"),
    ("hr.employee",            "EMP",  4, "never"),
    ("hr.payslip",             "PAY",  5, "monthly"),
    ("shop.order",             "ORD",  5, "yearly"),
    ("pos.order",              "POS",  5, "yearly"),
    ("pos.shift",              "SHIFT",5, "yearly"),
]

DEFAULT_SETTINGS = [
    ("core.timezone",    "string",  "Asia/Jakarta"),
    ("core.date_format", "string",  "DD/MM/YYYY"),
    ("core.number_format", "string","1.234,56"),
    ("inv.allow_negative_stock",    "bool", "false"),
    ("sal.default_payment_term_days","int", "30"),
    ("acc.lock_after_close",         "bool","true"),
    ("shop.allow_guest_checkout",    "bool","true"),
    ("cms.maintenance_mode",         "bool","false"),
]


def run_seed(app):
    with app.app_context():
        _seed_currency()
        company = _seed_company()
        _seed_role(company)
        _seed_sequences(company)
        _seed_settings()
        db.session.commit()
        print("[seed] core data seeded.")


def _seed_currency():
    currencies = [("IDR","Rupiah","Rp",0), ("USD","US Dollar","$",2),
                  ("SGD","Singapore Dollar","S$",2), ("EUR","Euro","€",2)]
    for code, name, symbol, dp in currencies:
        if not CoreCurrency.query.filter_by(code=code).first():
            db.session.add(CoreCurrency(code=code, name=name, symbol=symbol, decimal_places=dp))


def _seed_company():
    c = CoreCompany.query.filter_by(code="HQ").first()
    if not c:
        c = CoreCompany(code="HQ", legal_name="My Company", is_active=True)
        db.session.add(c)
        db.session.flush()
    return c


def _seed_role(company):
    if not CoreRole.query.filter_by(code="SUPERADMIN").first():
        db.session.add(CoreRole(code="SUPERADMIN", name="Super Admin",
                                is_system=True, company_id=company.id))


def _seed_sequences(company):
    for code, prefix, padding, reset in SEQUENCES:
        if not CoreSequence.query.filter_by(code=code, company_id=company.id).first():
            db.session.add(CoreSequence(
                company_id=company.id, code=code, prefix=prefix,
                padding=padding, reset_period=reset,
            ))


def _seed_settings():
    for key, vtype, value in DEFAULT_SETTINGS:
        if not CoreSetting.query.filter_by(scope="global", scope_id=None, key=key).first():
            db.session.add(CoreSetting(scope="global", key=key,
                                       value_type=vtype, value=value))
