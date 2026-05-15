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
    def get_menu_structure(cls) -> List[Dict[str, Any]]:
        """
        Generates a hierarchical menu structure for the app.
        Filters out child models by default unless they are explicitly in menu_groups.
        """
        # 1. Identify all models and their metadata
        models_by_table = {m.__tablename__: m for m in cls.models if hasattr(m, "__tablename__")}
        
        # 2. Get list of models that are NOT child tables
        # Or have an explicit __show_in_menu__ = True override
        visible_models = []
        for m in cls.models:
            if not hasattr(m, "__tablename__"):
                continue
            
            is_child = hasattr(m, "__parent__") and getattr(m, "__parent__") is not None
            show_override = getattr(m, "__show_in_menu__", False)
            
            if not is_child or show_override:
                visible_models.append(m.__tablename__)

        # 3. Build menu from menu_groups if defined
        structured_menu = []
        models_already_in_menu = set()

        if cls.menu_groups:
            for group in cls.menu_groups:
                group_items = []
                for model_name in group.get("models", []):
                    if model_name in models_by_table:
                        m = models_by_table[model_name]
                        group_items.append({
                            "type": "model",
                            "name": model_name,
                            "label": getattr(m, "__title__", model_name.replace("_", " ").title()),
                            "path": f"/{cls.app_name}/{model_name}",
                            "icon": getattr(m, "__icon__", "FileText")
                        })
                        models_already_in_menu.add(model_name)
                
                # Also handle nested sub-apps in menu groups if any
                for sub_app_name in group.get("apps", []):
                    # We'll just pass the name, frontend will need to fetch or use sidebar data
                    # But for now, let's just mark it as app
                    group_items.append({
                        "type": "app_link",
                        "name": sub_app_name,
                        "path": f"/{sub_app_name}"
                    })

                if group_items:
                    structured_menu.append({
                        "type": "group",
                        "label": group.get("label", "Group"),
                        "icon": group.get("icon", "Folder"),
                        "items": group_items
                    })

        # 4. Add remaining visible models that weren't in any group
        standalone_items = []
        for model_name in visible_models:
            if model_name not in models_already_in_menu and model_name not in ["auth_users", "sys_settings"]:
                m = models_by_table[model_name]
                standalone_items.append({
                    "type": "model",
                    "name": model_name,
                    "label": getattr(m, "__title__", model_name.replace("_", " ").title()),
                    "path": f"/{cls.app_name}/{model_name}",
                    "icon": getattr(m, "__icon__", "FileText")
                })
        
        if standalone_items:
            # Add as a default group or just items? 
            # Let's add them to a "General" group if there are other groups, 
            # otherwise just return them.
            if structured_menu:
                structured_menu.append({
                    "type": "group",
                    "label": "General",
                    "icon": "Layers",
                    "items": standalone_items
                })
            else:
                structured_menu.extend(standalone_items)

        return structured_menu

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
