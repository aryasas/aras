# -*- coding: utf-8 -*-
"""erp_config — module-level manifest.

Declares the module class. Models in this submodule can use:

    class Foo(ArasGen.Model, module=Config):
        ...

to inherit app/module/menu/icon defaults from this class.
"""
from app.erp import ERP


class Config(ERP):
    name  = "config"
    title = "Configuration"
    icon  = "fa-cogs"
    order = 0
