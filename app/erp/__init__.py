# -*- coding: utf-8 -*-
"""ERP — Aras Resource Planning. Submodules: erp_acc, erp_config, erp_crm, erp_main, erp_pos, erp_stock, erp_sup."""
from arasCore.arasgen import ArasGen

ARAS_AUTOLOAD = True


class ERP(ArasGen.App):
    """Root ERP app. Submodule manifests subclass this to inherit app metadata."""
    name  = "erp"
    title = "ERP"
    icon  = "fa-building"
    order = 10

    namespace_menus = {
        "cfg":    ("Settings",   "fa-cogs",          0),
        "main":   ("Settings",   "fa-cogs",          0),
        "acc":    ("Accounting", "fa-calculator",    1),
        "crm":    ("CRM",        "fa-handshake-o",   2),
        "sup":    ("Supplier",   "fa-truck",         3),
        "pos":    ("arasPos",    "fa-shopping-cart", 4),
        "stock":  ("Stock",      "fa-cubes",         6),
        "report": ("Reports",    "fa-bar-chart",     5),
    }
    namespace_aliases = {"stk": "stock"}
