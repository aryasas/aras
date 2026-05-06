# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/__init__.py
=============================
Single entrypoint for the framework. Apps do:

    from arasCore import ArasGen

    class User(ArasGen.Model):
        __tablename__ = "auth_users"
        username = ArasGen.String(unique=True, null=False, index=True)
        password = ArasGen.Password(null=False)

The ``ArasGen`` namespace bundles Model, Form, Route, DB, and field
descriptors so a single import covers every framework concern.
"""
from __future__ import annotations
from functools import partial

from .fields import Col
from .fields import (
    String   as _t_String,   Text     as _t_Text,
    Integer  as _t_Integer,  Decimal  as _t_Decimal,
    Float    as _t_Float,    Boolean  as _t_Boolean,
    Date     as _t_Date,     DateTime as _t_DateTime,
    Password as _t_Password, Email    as _t_Email,
    Select   as _t_Select,   FK       as _t_FK,
)
from .model import ArasModel
from .form  import ArasForm
from .route import ArasRoute
from .db    import ArasDB
from .registry import auto_resources, auto_menu_groups
from .app      import ArasApp


def _typed(token):
    """Col factory bound to a specific type token."""
    f = partial(Col, token)
    f.__doc__ = f"Col with type={token.name}."
    return f


class ArasGen:
    """Umbrella namespace — the only import an app ever needs."""

    # Bases
    Model = ArasModel
    Form  = ArasForm
    Route = ArasRoute
    DB    = ArasDB
    AppClass = ArasApp   # subclass-style app declaration

    # Manifest sugar — short reach into ArasRoute
    App         = ArasRoute.App
    Menu        = ArasRoute.Menu
    Resource    = ArasRoute.Resource
    Handler     = ArasRoute.Handler
    CustomRoute = ArasRoute.Route

    # Auto manifest emitters from declarative models
    auto_resources   = staticmethod(auto_resources)
    auto_menu_groups = staticmethod(auto_menu_groups)

    # Field descriptor + typed shortcuts
    Col      = Col
    String   = _typed(_t_String)
    Text     = _typed(_t_Text)
    Integer  = _typed(_t_Integer)
    Decimal  = _typed(_t_Decimal)
    Float    = _typed(_t_Float)
    Boolean  = _typed(_t_Boolean)
    Date     = _typed(_t_Date)
    DateTime = _typed(_t_DateTime)
    Password = _typed(_t_Password)
    Email    = _typed(_t_Email)
    Select   = _typed(_t_Select)
    FK       = _typed(_t_FK)



# Module-level factories — `from arasCore.aras_gen import String` returns a factory, not a token.
String = ArasGen.String
Text = ArasGen.Text
Integer = ArasGen.Integer
Decimal = ArasGen.Decimal
Float = ArasGen.Float
Boolean = ArasGen.Boolean
Date = ArasGen.Date
DateTime = ArasGen.DateTime
Password = ArasGen.Password
Email = ArasGen.Email
Select = ArasGen.Select
FK = ArasGen.FK

__all__ = [
    "ArasGen", "ArasModel", "ArasForm", "ArasRoute", "ArasDB", "ArasApp",
    "Col", "String", "Text", "Integer", "Decimal", "Float", "Boolean",
    "Date", "DateTime", "Password", "Email", "Select", "FK",
    "auto_resources", "auto_menu_groups",
]
