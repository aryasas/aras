from core import Aras
from .models import Company, Currency, Uom, PriceType, Charge, ExchangeRate, Setting, ModeOfPayment, PrintTemplate, Report, Notification

class CompanyView(Aras.View):
    model = Company
    title = "Companies"
    icon = "pi pi-building"

class CurrencyView(Aras.View):
    model = Currency
    title = "Currencies"
    icon = "pi pi-money-bill"

class UomView(Aras.View):
    model = Uom
    title = "Units of Measure"
    icon = "pi pi-tag"

class PriceTypeView(Aras.View):
    model = PriceType
    title = "Price Types"
    icon = "pi pi-list"

class ChargeView(Aras.View):
    model = Charge
    title = "Taxes & Charges"
    icon = "pi pi-percentage"
    layout = [
        {"title": "Configuration", "fields": ["name", "charge_type", "calc_method", "rate", "amount"]},
        {"title": "Accounting", "fields": ["account_collected_id", "account_paid_id"]},
        {"title": "Behavior", "fields": ["is_inclusive", "is_compound", "sequence"]}
    ]

class ExchangeRateView(Aras.View):
    model = ExchangeRate
    title = "Exchange Rates"
    icon = "pi pi-chart-line"

class SettingView(Aras.View):
    model = Setting
    title = "Settings"
    icon = "pi pi-sliders-h"


class ModeOfPaymentView(Aras.View):
    model = ModeOfPayment
    title = "Payment Modes"
    icon = "pi pi-credit-card"

class PrintTemplateView(Aras.View):
    model = PrintTemplate
    title = "Print Templates"
    icon = "pi pi-print"

class ReportView(Aras.View):
    model = Report
    title = "Reports"
    icon = "pi pi-file-edit"

class NotificationView(Aras.View):
    model = Notification
    title = "Notifications"
    icon = "pi pi-bell"

