# claude-opus-4-8
"""
core.workspace — the framework's built-in Workspace configuration app.

This is framework tier (formerly apps/core_config). It is `required=True` and
imports only from core.*, so it ships with the framework regardless of which
product apps are installed. It is registered explicitly at boot via
`register_framework_apps()` (NOT product discovery, which only scans apps/).
"""
from .app import CoreConfigApp

__all__ = ["CoreConfigApp"]
