# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/route.py
==========================
Manifest helpers — thin namespace over existing app_helper primitives.
"""
from __future__ import annotations

try:
    from arasCore.lib.services.app_helper import (
        AppHelper, MenuGroup, ResourceDef, SubHandler, CustomRoute,
    )
except Exception:                       # pragma: no cover
    AppHelper = MenuGroup = ResourceDef = SubHandler = CustomRoute = None


class ArasRoute:
    """Namespace for app manifest declarations."""
    App      = AppHelper
    Menu     = MenuGroup
    Resource = ResourceDef
    Handler  = SubHandler
    Route    = CustomRoute


__all__ = ["ArasRoute"]
