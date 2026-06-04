# claude-sonnet-4-6
"""
Framework app-configuration interface.

Lets apps own a typed, per-organization config model and lets the framework
read/serve it BY KEY without ever importing the app — preserving the hard
invariant `core/ never imports apps/`. Mirrors the existing ServiceRegistry
pattern already proven in this codebase.
"""
from .app_config import AppConfig
from .registry import AppConfigRegistry, app_config_registry

__all__ = ["AppConfig", "AppConfigRegistry", "app_config_registry"]
