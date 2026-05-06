# -*- coding: utf-8 -*-
"""
arasCore/lib/core/aras_route.py
===============================
Proxy for App Framework route and manifest helpers.
"""

try:
    from arasCore.lib.services.app_helper import AppHelper, MenuGroup, ResourceDef, SubHandler, CustomRoute
except ImportError:
    AppHelper = MenuGroup = ResourceDef = SubHandler = CustomRoute = None

class ArasRoute:
    """Namespace for application manifest and routing helpers."""
    App      = AppHelper
    Menu     = MenuGroup
    Resource = ResourceDef
    Handler  = SubHandler
    Route    = CustomRoute
