from core import Aras
from core.workspace.models import Organization, Currency, PrintTemplate, Notification
from plugins.commerce.models import Uom, PriceType, Charge, ExchangeRate, ModeOfPayment
from core.auth.access import UserAccess

class OrganizationView(Aras.View):
    model = Organization
    title = "Organizations"
    icon = "Building"
    fields = {
        "profile": {"ui_type": "profile_picker"},
        "unit_type": {"ui_type": "unit_type_picker"},
    }
    layout = [
        {"title": "Identity", "fields": ["code", "name", "legal_name", "trade_name", "tax_id", "is_group", "parent_id", "profile", "unit_type"]},
        {"title": "Contact & Branding", "fields": ["phone", "email", "website", "address", "logo_path"]},
        {"title": "Configuration", "fields": ["base_currency_id", "fiscal_year_start_month", "default_coa_template", "default_charge_id", "default_charge_enable"]},
        {"title": "Accounting & Stock Behavior", "fields": ["enable_perpetual_inventory", "enable_provisional_non_stock", "avg_cost_by_location", "allow_zero_stock"]},
        {"title": "Default Accounts", "actions": ["inherit_accounts", "fill_default_accounts"], "fields": [
            "acc_bank_default_id", "acc_cash_default_id", "acc_receivable_default_id", "acc_payable_default_id",
            "acc_income_default_id", "acc_cogs_default_id", "acc_inventory_default_id",
            "acc_payroll_payable_id", "acc_payment_discount_id", "acc_write_off_id",
            "acc_unrealized_gain_loss_id", "acc_round_off_id"
        ]},
        {"title": "Stock Accounts", "fields": [
            "acc_stock_received_not_billed_id", "acc_stock_provisional_id", "acc_stock_adjustment_id",
            "acc_expenses_in_valuation_id", "acc_stock_default_id"
        ]},
        {"title": "Tax Accounts", "fields": ["acc_tax_output_ppn_id", "acc_tax_input_ppn_id"]},
    ]

class CurrencyView(Aras.View):
    model = Currency
    title = "Currencies"
    icon = "Banknote"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "code", "symbol"],
        },
    ]

class UomView(Aras.View):
    model = Uom
    title = "Units of Measure"
    icon = "Tag"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "abbreviation", "category"],
        },
    ]

class PriceTypeView(Aras.View):
    model = PriceType
    title = "Price Types"
    icon = "List"

class ChargeView(Aras.View):
    model = Charge
    title = "Taxes & Charges"
    icon = "Percent"
    layout = [
        {"title": "Configuration", "fields": ["name", "charge_type", "calc_method", "rate", "amount"]},
        {"title": "Accounting", "fields": ["account_collected_id", "account_paid_id"]},
        {"title": "Behavior", "fields": ["is_inclusive", "is_compound"]}
    ]

class ExchangeRateView(Aras.View):
    model = ExchangeRate
    title = "Exchange Rates"
    icon = "TrendingUp"
    fields = {
        "org_id": {"ui_type": "org_picker"},
    }
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["org_id", "currency_id", "rate", "date"],
        },
    ]


class ModeOfPaymentView(Aras.View):
    model = ModeOfPayment
    title = "Payment Modes"
    icon = "CreditCard"
    fields = {
        "org_id": {"ui_type": "org_picker"},
    }
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["org_id", "name", "payment_type", "config_payment_accounts"],
        },
    ]

class PrintTemplateView(Aras.View):
    model = PrintTemplate
    title = "Print Templates"
    icon = "Printer"
    fields = {
        "org_id": {"ui_type": "org_picker"},
    }
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["org_id", "name", "template_type", "content"],
        },
    ]

class NotificationView(Aras.View):
    model = Notification
    title = "Notifications"
    icon = "Bell"
    fields = {
        "org_id": {"ui_type": "org_picker"},
    }

class UserAccessView(Aras.View):
    model = UserAccess
    title = "User Access"
    icon = "ShieldCheck"
    fields = {
        "org_id": {"ui_type": "org_picker"},
    }
