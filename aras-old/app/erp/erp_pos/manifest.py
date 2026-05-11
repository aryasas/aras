# -*- coding: utf-8 -*-
"""erp_pos — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Pos):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Pos(ERP):
    name  = "pos"
    title = "arasPos"
    icon  = "fa-shopping-cart"
    order = 4
