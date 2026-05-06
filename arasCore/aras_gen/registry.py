# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/registry.py
=============================
Class-level registry for ArasModel subclasses.

Why this exists
---------------
With the lean DSL a developer declares ONE class:

    class Customer(ArasModel):
        __app__   = "erp"
        __menu__  = "Sales"        # optional: group title in sidebar / app home
        __title__ = "Customers"    # optional: human label
        __url__   = "crm/customer" # optional: URL slug; default = kebab(class_name)
        __icon__  = "fa-user"
        name = String(null=False)

The framework reads this registry at manifest-build time and emits
`ResourceDef` / `MenuGroup` automatically — no manual route wiring,
no separate menu list. One source of truth.

Functions
---------
register(model)            : called by metaclass; appends to _MODELS
models_for(app)            : list models declared with __app__ == app
auto_resources(app)        : -> [ResourceDef] for that app
auto_menu_groups(app)      : -> [MenuGroup] grouped by __menu__
"""
from __future__ import annotations
from typing import List, Type
import re

_MODELS: list[type] = []   # populated by ArasModel metaclass


# ── public registration ─────────────────────────────────────────────────────

def register(model: type) -> None:
    """Register an ArasModel subclass. Idempotent."""
    if model not in _MODELS:
        _MODELS.append(model)


def models_for(app: str) -> List[type]:
    """Return all registered models whose __app__ matches `app`."""
    return [m for m in _MODELS if getattr(m, "__app__", None) == app]


# ── helpers ─────────────────────────────────────────────────────────────────

def _kebab(name: str) -> str:
    """CamelCase → kebab-case  (e.g. ModeOfPayment → mode-of-payment)."""
    s = re.sub(r"(.)([A-Z][a-z]+)", r"\1-\2", name)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", s)
    return s.lower()


def _title(name: str) -> str:
    """CamelCase → 'Camel Case'."""
    return re.sub(r"(?<!^)(?=[A-Z])", " ", name).strip()


def _meta(model: type) -> dict:
    """Pull declarative meta off a model with safe defaults."""
    cls_name = model.__name__
    return {
        "app":           getattr(model, "__app__",   None),
        "menu":          getattr(model, "__menu__",  None),
        "title":         getattr(model, "__title__", _title(cls_name)),
        "url":           getattr(model, "__url__",   _kebab(cls_name)),
        "icon":          getattr(model, "__icon__",  "fa-table"),
        "admin_list":    getattr(model, "__admin_list__",    True),
        "is_child":      getattr(model, "__is_child__",      False),
        "searchable":    list(getattr(model, "__searchable__", []) or []),
        "filters":       list(getattr(model, "__filters__",    []) or []),
        "menu_order":    getattr(model, "__menu_order__",     50),
    }


# ── manifest emitters ───────────────────────────────────────────────────────

def auto_resources(app: str) -> list:
    """Build a flat ResourceDef list for `app` from registered models."""
    from .route import ArasRoute
    Resource = ArasRoute.Resource
    out = []
    for m in models_for(app):
        meta = _meta(m)
        out.append(Resource(
            meta["url"],
            m,
            admin_list     = meta["admin_list"] and not meta["is_child"],
            is_child_table = meta["is_child"],
            menu_title     = meta["title"],
            menu_icon      = meta["icon"],
            searchable     = meta["searchable"],
            filters        = meta["filters"],
        ))
    return out


def auto_menu_groups(app: str) -> list:
    """Build MenuGroup list grouped by __menu__. Models without __menu__ go
    into a default group named after the app."""
    from .route import ArasRoute
    Menu, Resource = ArasRoute.Menu, ArasRoute.Resource

    buckets: dict[str, list] = {}
    orders:  dict[str, int]  = {}

    for m in models_for(app):
        meta = _meta(m)
        if meta["is_child"]:                  # child tables stay accessible but
            grp_name = meta["menu"] or "_"    # group "_" = silent (admin_list=False)
        else:
            grp_name = meta["menu"] or app.title()
        buckets.setdefault(grp_name, []).append(Resource(
            meta["url"], m,
            admin_list     = meta["admin_list"] and not meta["is_child"],
            is_child_table = meta["is_child"],
            menu_title     = meta["title"],
            menu_icon      = meta["icon"],
            searchable     = meta["searchable"],
            filters        = meta["filters"],
        ))
        orders[grp_name] = min(orders.get(grp_name, 999), meta["menu_order"])

    return [
        Menu(name, "fa-folder", order=orders[name], resources=res)
        for name, res in buckets.items() if name != "_"
    ]


__all__ = ["register", "models_for", "auto_resources", "auto_menu_groups"]
