"""
Purpose: Level 2 Base App class for all application modules.
Context: Inherits from Aras (Level 1). Scanned by Manager for registration.
Impact: Standardizes how applications declare their manifest and models.
"""
from typing import List, Any, Dict, Type
from .aras import Aras

class App(Aras):
    """
    Level 2 Core App.
    Inherits from Aras (Level 1).
    Abstract base for application modules (ERP, CRM, Admin).
    """
    __abstract__ = True
    _registry: Dict[str, Type['App']] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Automatically register non-abstract subclasses
        if not cls.__dict__.get("__abstract__"):
            App._registry[cls.__name__] = cls

    app_name: str = ""
    parent_name: str = "" # Reference to a parent app name
    app_label: str = ""
    description: str = ""
    version: str = "1.0.0"
    icon: str = "Package"
    have_home: bool = False
    models: List[Any] = []
    menu_groups: List[Dict[str, Any]] = [] # [{"label": "Group", "icon": "Icon", "models": ["table_name"]}]

    @classmethod
    def get_manifest(cls) -> dict:
        """Generates the application manifest for the registry sync engine."""
        return {
            "name": cls.app_name,
            "parent_name": cls.parent_name,
            "label": cls.app_label,
            "description": cls.description,
            "version": cls.version,
            "icon": cls.icon,
            "have_home": cls.have_home,
            "models": [m.__tablename__ for m in cls.models if hasattr(m, "__tablename__")],
            "menu_groups": cls.menu_groups
        }
