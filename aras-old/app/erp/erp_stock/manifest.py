# -*- coding: utf-8 -*-
"""erp_stock — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Stock):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Stock(ERP):
    name  = "stock"
    title = "Stock"
    icon  = "fa-cubes"
    order = 6
