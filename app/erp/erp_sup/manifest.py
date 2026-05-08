# -*- coding: utf-8 -*-
"""erp_sup — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Sup):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Sup(ERP):
    name  = "sup"
    title = "Supplier"
    icon  = "fa-truck"
    order = 3
