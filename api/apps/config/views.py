from core import Aras
from .models import Organization, Currency, Uom, PriceType, Charge, ExchangeRate, Setting, ModeOfPayment, PrintTemplate, Notification

class OrganizationView(Aras.View):
    model = Organization
    title = "Organizations"
    icon = "Building"
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
        {"title": "Formatting Defaults", "fields": ["date_format", "number_format", "decimal_precision"]}
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
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["currency_id", "rate", "date"],
        },
    ]

class SettingView(Aras.View):
    model = Setting
    title = "Settings"
    icon = "Sliders"


class ModeOfPaymentView(Aras.View):
    model = ModeOfPayment
    title = "Payment Modes"
    icon = "CreditCard"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "payment_type", "erp_config_payment_accounts"],
        },
    ]

class PrintTemplateView(Aras.View):
    model = PrintTemplate
    title = "Print Templates"
    icon = "Printer"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "template_type", "content"],
        },
    ]

class NotificationView(Aras.View):
    model = Notification
    title = "Notifications"
    icon = "Bell"
