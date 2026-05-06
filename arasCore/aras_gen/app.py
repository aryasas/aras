# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/app.py
========================
ArasApp — declarative class for an entire app.

Mirrors the ArasModel pattern: instead of instantiating
`helper = AppHelper(name="todo", ...)`, an app subclasses ArasApp:

    class Todo(ArasApp):
        name        = "todo"
        title       = "Todo"
        icon        = "fa-check-square-o"
        order       = 30
        # menus / resources / custom_routes are auto-derived from
        # registered ArasModels with __app__ == name. Override only if needed:
        # menu_groups   = [...]   (skips auto-derivation)
        # custom_routes = [...]
        # settings_schema = [...]

The metaclass compiles the class into an AppHelper instance accessible via
`Todo.helper`. Manifest files become a one-liner:

    # app/todo/manifest.py
    from app.todo.app import Todo
    helper = Todo.helper

Why a class, not a function call?
- Symmetric with ArasModel — every aras concern is a class.
- Subclasses can override single attributes cleanly.
- Future hooks (lifecycle, perms, theming) attach to the class, not kwargs.
"""
from __future__ import annotations
from typing import ClassVar, List

from .registry import auto_menu_groups, auto_resources
from .route    import ArasRoute


# ── Sentinel — distinguishes "not declared" from "explicitly empty" ─────────
_AUTO = object()


class _ArasAppMeta(type):
    """Compile an ArasApp subclass to an AppHelper instance on class creation."""

    def __new__(mcs, cls_name, bases, ns):
        cls = super().__new__(mcs, cls_name, bases, ns)
        # Skip the ArasApp base itself
        if ns.get("__abstract__", False) or cls_name == "ArasApp":
            return cls

        name = ns.get("name") or getattr(cls, "name", None)
        if not name:                                # not a concrete app class
            return cls

        AppHelper = ArasRoute.App
        if AppHelper is None:                       # framework half-initialised
            return cls

        # Auto-derive from registry unless the class supplied its own
        menu_groups   = ns.get("menu_groups",   _AUTO)
        resources     = ns.get("resources",     _AUTO)
        custom_routes = ns.get("custom_routes", [])

        if menu_groups is _AUTO and resources is _AUTO:
            menu_groups = auto_menu_groups(name)
            resources   = None
        else:
            menu_groups = None if menu_groups is _AUTO else menu_groups
            resources   = None if resources   is _AUTO else resources

        cls.helper = AppHelper(
            name            = name,
            title           = ns.get("title", name.title()),
            resources       = resources,
            menu_groups     = menu_groups,
            custom_routes   = custom_routes,
            admin_icon      = ns.get("icon",  "fa-cubes"),
            admin_order     = ns.get("order", 99),
            home_url        = ns.get("home_url"),
            settings_schema = ns.get("settings_schema") or [],
            admin_slug      = ns.get("admin_slug"),
            api_slug        = ns.get("api_slug"),
            template        = ns.get("template"),
        )
        return cls


class ArasApp(metaclass=_ArasAppMeta):
    """Subclass to declare an app. Set `name` (slug) and optional cosmetics.

    Auto-derives menu_groups from ArasModels whose `__app__` matches `name`.
    Override `menu_groups` or `resources` to take manual control.
    """
    __abstract__: ClassVar[bool] = True

    name:  ClassVar[str]  = ""
    title: ClassVar[str]  = ""
    icon:  ClassVar[str]  = "fa-cubes"
    order: ClassVar[int]  = 99


__all__ = ["ArasApp"]
