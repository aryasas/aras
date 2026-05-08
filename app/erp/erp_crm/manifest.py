# -*- coding: utf-8 -*-
"""erp_crm — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Crm):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Crm(ERP):
    name  = "crm"
    title = "CRM"
    icon  = "fa-handshake-o"
    order = 2
