# -*- coding: utf-8 -*-
"""
arasCore.lib.arasgen
====================
Library package — internal split of the ArasGen framework.

External code imports `from arasCore.arasgen import ArasGen` (single-file
shim at arasCore/arasgen.py). Internals here are split for maintainability
and future pip-package extraction.

Layout:
    core/   shared primitives (Col, fields, infer, labels, _Type, ArasDB)
    model/  ArasModel + mixins (audit, naming, fetch, list, write, ...)
    form/   ArasForm + WTForms-shape proxy
    route/  ArasRoute + ArasApp + auto-discovery
"""
from arasCore.lib.arasgen.core   import (
    Col, String, Text, Integer, Decimal, Float, Boolean,
    Date, DateTime, Password, Email, Select, FK,
    infer_type, resolve_label, ArasDB,
)
from arasCore.lib.arasgen.model  import ArasModel, register, models_for
from arasCore.lib.arasgen.form   import ArasForm
from arasCore.lib.arasgen.route  import ArasRoute, ArasApp, register_app_config, auto_resources, auto_menu_groups
from arasCore.arasgen import ArasGen

__all__ = [
    "Col", "String", "Text", "Integer", "Decimal", "Float", "Boolean",
    "Date", "DateTime", "Password", "Email", "Select", "FK",
    "infer_type", "resolve_label", "ArasDB",
    "ArasModel", "register", "models_for",
    "ArasForm",
    "ArasRoute", "ArasApp", "register_app_config",
    "auto_resources", "auto_menu_groups", "ArasGen",
]
