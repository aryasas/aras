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

ArasGen.autodiscover(__name__)


# Run ERP seed on remigrate (formerly hardcoded in arasCore/lib/cli/cli_db.py)
def _on_remigrate(obj=None, **kwargs):
    try:
        from app.erp.erp_main.seed import run_seed
        run_seed(obj)
    except Exception:
        pass

from arasCore.lib.core.events import on as _on_event
_on_event("framework.remigrate", _on_remigrate)
