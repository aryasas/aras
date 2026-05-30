# gemini-flash
import os
import json
import logging
from dataclasses import dataclass
from typing import Dict, Optional
from .base_registry import Registry

logger = logging.getLogger(__name__)

@dataclass
class I18nBundle:
    app: str
    lang: str
    translations: dict

class I18nRegistry(Registry[I18nBundle]):
    """Registry for internationalization bundles."""
    
    def load_from_app(self, app_cls):
        """
        Scans api/apps/<app>/locales/<lang>.json and registers bundles.
        """
        app_name = getattr(app_cls, "app_name", None)
        if not app_name:
            return

        # Try to find the app directory. This is a bit heuristic.
        # Usually apps are in api/apps/<app_name>
        # but could be api/apps/erp/<app_name> etc.
        # We'll use the module path if available.
        module_path = app_cls.__module__
        module_parts = module_path.split(".")
        
        # Heuristic: find 'apps' in module parts and look relative to that
        try:
            apps_idx = module_parts.index("apps")
            app_dir_parts = module_parts[apps_idx:apps_idx+2] # ['apps', 'core_config'] or ['apps', 'erp']
            
            # This is still not perfect if it's deeply nested.
            # Let's try to get the file path of the module.
            import sys
            module = sys.modules.get(module_path)
            if module and hasattr(module, "__file__"):
                app_root = os.path.dirname(module.__file__)
                locales_dir = os.path.join(app_root, "locales")
                
                if os.path.exists(locales_dir) and os.path.isdir(locales_dir):
                    for filename in os.listdir(locales_dir):
                        if filename.endswith(".json"):
                            lang = filename[:-5]
                            filepath = os.path.join(locales_dir, filename)
                            try:
                                with open(filepath, 'r', encoding='utf-8') as f:
                                    translations = json.load(f)
                                    bundle = I18nBundle(app=app_name, lang=lang, translations=translations)
                                    self.register(app_name, lang, bundle)
                                    logger.info(f"Loaded i18n bundle for {app_name} [{lang}]")
                            except Exception as e:
                                logger.error(f"Failed to load i18n bundle {filepath}: {e}")
        except (ValueError, IndexError):
            pass

# Singleton instance
i18n_registry = I18nRegistry()
