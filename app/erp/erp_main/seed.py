"""Seed core data: default company, IDR currency, SUPERADMIN role, sequences."""
from arasCore.lib.core.extensions import db
from app.erp.erp_config.models.company import Company
from app.erp.erp_config.models.currency import Currency
from app.erp.erp_main.models.acl import ErpRole
from app.erp.erp_main.models.doc_series import DocSeries as Sequence
from app.erp.erp_main.models.setting import Setting


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
    ("stock.move",             "SM",   5, "yearly"),
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
    ("erp.accounting_mode_hpp",      "bool","false"),
    ("erp.account_revenue_default",  "int", "0"),
    ("erp.account_purchase_default", "int", "0"),
    ("erp.account_cogs_default",     "int", "0"),
]


from app.erp.erp_main.report_seed import run_seed as seed_reports

def run_seed(app):
    with app.app_context():
        _seed_currency()
        company = _seed_company()
        _seed_role(company)
        _seed_sequences(company)
        _seed_settings()
        _seed_system_formatting()
        _seed_customer(company)
        _seed_supplier(company)
        seed_reports()
        db.session.commit()
        print("[seed] core data seeded.")


def _seed_system_formatting():
    """Seed global framework formatting into ArasSystemSetting."""
    from arasCore.admin.models import ArasSystemSetting
    
    defaults = [
        ("core.date_format", "DD/MM/YYYY", "Global Date Format", "e.g. DD/MM/YYYY or YYYY-MM-DD"),
        ("core.number_format", "#,###.##", "Global Number Format", "e.g. 1.234,56 or 1,234.56"),
        ("core.decimal_precision", "2", "Global Decimal Precision", "Default decimal places for numbers")
    ]
    
    for key, val, label, help_text in defaults:
        ArasSystemSetting.set(
            key, val, 
            value_type="integer" if "precision" in key else "string",
            label=label, 
            help_text=help_text,
            section="formatting"
        )


def _seed_currency():
    for code, name, symbol, dp in [
        ("IDR","Rupiah","Rp",0), ("USD","US Dollar","$",2),
        ("SGD","Singapore Dollar","S$",2), ("EUR","Euro","€",2)
    ]:
        Currency.get_or_create({"name": name, "symbol": symbol, "decimal_places": dp}, code=code)


def _seed_company():
    c, _ = Company.get_or_create({"legal_name": "My Company", "is_active": True}, code="HQ")
    return c


def _seed_role(company):
    ErpRole.get_or_create({"name": "Super Admin", "is_system": True, "company_id": company.id},
                          code="SUPERADMIN")


def _seed_sequences(company):
    for code, prefix, padding, reset in SEQUENCES:
        Sequence.get_or_create(
            {"prefix": prefix, "padding": padding, "reset_period": reset},
            code=code, company_id=company.id,
        )


def _seed_settings():
    for key, vtype, value in DEFAULT_SETTINGS:
        Setting.get_or_create(
            {"value_type": vtype, "value": value},
            scope="global", scope_id=None, key=key,
        )


def _seed_customer(company):
    from app.erp.erp_crm.models import CrmCustomer
    CrmCustomer.get_or_create(
        {"name": "Walk-in Customer", "type": "individual"},
        company_id=company.id, code="CUST-001",
    )


def _seed_supplier(company):
    from app.erp.erp_sup.models import SupSupplier
    SupSupplier.get_or_create(
        {"name": "Default Supplier", "type": "company"},
        company_id=company.id, code="SUP-001",
    )
