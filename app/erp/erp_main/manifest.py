# -*- coding: utf-8 -*-
"""erp_main — module-level manifest.

Holds shared admin/configuration models (DocSeries, Fiscal, Roles, MOP, Settings,
PrintTemplate, ErpReport, etc). Default __menu__ is "Configuration"; the
Print/Report models override to "Reports".
"""
from app.erp import ERP


class Main(ERP):
    name  = "main"
    title = "Configuration"
    icon  = "fa-cogs"
    order = 0
