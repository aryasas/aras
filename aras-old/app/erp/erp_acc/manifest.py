# -*- coding: utf-8 -*-
"""erp_acc — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Acc):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Acc(ERP):
    name  = "acc"
    title = "Accounting"
    icon  = "fa-calculator"
    order = 1
