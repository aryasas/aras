# -*- coding: utf-8 -*-
from arasCore.lib.core import ArasGen

from app.erp.erp_core.models.tax import Charge
from app.erp.erp_core.models import (
    Company,
    Currency, FxRate,
    Setting, Sequence,
    FiscalYear, FiscalPeriod,
    ErpRole, ErpPermission,
    Attachment, PrintTemplate,
    ErpReport,
)
from app.erp.erp_core.models.payment_mode import ModeOfPayment

menu_groups = [
    ArasGen.Menu("Settings", "fa-cogs", order=0, resources=[
        ArasGen.Resource("company",        Company,       admin_list=True,
                    menu_title="Company", menu_icon="fa-building-o"),
        ArasGen.Resource("currency",       Currency,      admin_list=True,
                    menu_title="Currency", menu_icon="fa-dollar"),
        ArasGen.Resource("fx-rate",        FxRate,        admin_list=False, is_child_table=True),
        ArasGen.Resource("fiscal-year",    FiscalYear,    admin_list=True,
                    menu_title="Fiscal Year", menu_icon="fa-calendar"),
        ArasGen.Resource("fiscal-period",  FiscalPeriod,  admin_list=False, is_child_table=True),
        ArasGen.Resource("sequence",       Sequence,      admin_list=True,
                    menu_title="Sequences", menu_icon="fa-sort-numeric-asc"),
        ArasGen.Resource("print-template", PrintTemplate, admin_list=True,
                    menu_title="Print Templates", menu_icon="fa-print"),
        ArasGen.Resource("role",           ErpRole,          admin_list=True,
                    menu_title="Roles", menu_icon="fa-shield"),
        ArasGen.Resource("permission",     ErpPermission,    admin_list=True,
                    menu_title="Permissions", menu_icon="fa-key"),
        ArasGen.Resource("setting",        Setting,       admin_list=False),
        ArasGen.Resource("attachment",     Attachment,    admin_list=False),
        ArasGen.Resource("charge",         Charge,          admin_list=True,
                    menu_title="Charges", menu_icon="fa-percent"),
        ArasGen.Resource("payment-mode",   ModeOfPayment,   admin_list=True,
                    menu_title="Mode of Payment", menu_icon="fa-credit-card"),
    ]),
    ArasGen.Menu("Reports", "fa-bar-chart", order=5, resources=[
        ArasGen.Resource("report", ErpReport, admin_list=True,
                    menu_title="Report Templates", menu_icon="fa-file-text-o"),
    ]),
]

custom_routes = []

settings_schema = [
    {"key": "company_name",      "label": "Company Name",          "value_type": "string",  "default": "",     "order": 1},
    {"key": "default_currency",  "label": "Default Currency",      "value_type": "string",  "default": "IDR",  "order": 2},
    {"key": "fiscal_year_start", "label": "Fiscal Year Start (MM-DD)", "value_type": "string", "default": "01-01", "order": 3},
    {"key": "tax_inclusive",     "label": "Tax Inclusive Pricing",  "value_type": "boolean", "default": False,  "order": 4},
    {"key": "enable_multi_currency", "label": "Enable Multi-Currency", "value_type": "boolean", "default": False, "order": 5},
    {"key": "low_stock_alert",   "label": "Low Stock Alert Threshold", "value_type": "integer", "default": 10,  "order": 6},
    {"key": "report_footer",     "label": "Report Footer Text",    "value_type": "text",    "default": "",     "order": 7},
]