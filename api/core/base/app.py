"""
Purpose: Level 2 Base App class for all application modules.
Context: Inherits from Aras (Level 1). Scanned by Manager for registration.
Impact: Standardizes how applications declare their manifest and models.
"""
from typing import List, Any, Dict, Type
from .aras import Aras
from ..lib.helpers import to_label_case

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
    app_type: str = "app"  # "framework" | "app" | "module"
    table_prefix: str = ""  # Override for stripping tablename prefix (e.g. "erp_accounting" when app_name is "accounting")
    app_label: str = ""
    description: str = ""
    version: str = "1.0.0"
    icon: str = "Package"
    have_home: bool = False
    requires: List[str] = []  # App names this app depends on (e.g. ["accounting"])
    # Features that are off by default and require another app to be active.
    # Key = org config field name, value = required app name.
    # e.g. {"enable_perpetual_inventory": "accounting", "enable_auto_journal": "accounting"}
    optional_features: Dict[str, str] = {}
    models: List[Any] = []
    menu_groups: List[Dict[str, Any]] = [] # [{"label": "Group", "icon": "Icon", "models": ["table_name"]}]

    @classmethod
    def _get_clean_label(cls, name: str) -> str:
        """Strips app and parent prefixes from a name and titles it."""
        clean = name
        if cls.app_name and clean.startswith(f"{cls.app_name}_"):
            clean = clean[len(cls.app_name)+1:]
        if cls.parent_name and clean.startswith(f"{cls.parent_name}_"):
            clean = clean[len(cls.parent_name)+1:]
        return to_label_case(clean)

    @classmethod
    def _get_clean_path(cls, model_name: str = None) -> str:
        """Generates a hierarchical hyphenated path for the app or model."""
        segments = []
        if cls.parent_name:
            segments.append(cls.parent_name.replace("_", "-"))
        
        # App name segment (strip parent prefix if present)
        app_seg = cls.app_name
        if cls.parent_name and app_seg.startswith(f"{cls.parent_name}_"):
            app_seg = app_seg[len(cls.parent_name)+1:]
        segments.append(app_seg.replace("_", "-"))
        
        if model_name:
            # Model segment (strip longest matching prefix first)
            model_seg = model_name
            full_prefix = f"{cls.parent_name}_{cls.app_name}_" if cls.parent_name and cls.app_name else None
            if cls.table_prefix and model_seg.startswith(f"{cls.table_prefix}_"):
                model_seg = model_seg[len(cls.table_prefix)+1:]
            elif full_prefix and model_seg.startswith(full_prefix):
                model_seg = model_seg[len(full_prefix):]
            elif cls.app_name and model_seg.startswith(f"{cls.app_name}_"):
                model_seg = model_seg[len(cls.app_name)+1:]
            elif cls.parent_name and model_seg.startswith(f"{cls.parent_name}_"):
                model_seg = model_seg[len(cls.parent_name)+1:]
            segments.append(model_seg.replace("_", "-"))
            
        return "/" + "/".join(segments)

    @classmethod
    def _view_label(cls, model_name: str, model_cls) -> str:
        """Resolve menu label via View registry, falling back to clean label."""
        from ..base.view import View
        view_cls = View._auto_register(model_cls)
        return view_cls.title or cls._get_clean_label(model_name)

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
            from ..base.view import View as _View
            _view_cls = _View._view_map.get(m.__tablename__)
            show_override = (getattr(_view_cls, "standalone", False) if _view_cls else False) or getattr(m, "__show_in_menu__", False)
            
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
                            "label": cls._view_label(model_name, m),
                            "path": cls._get_clean_path(model_name),
                            "icon": getattr(m, "__icon__", "FileText")
                        })
                        models_already_in_menu.add(model_name)
                
                # Also handle nested sub-apps in menu groups if any
                for sub_app_name in group.get("apps", []):
                    # For sub-apps, we find the registered app class to get its clean path
                    sub_app_cls = App._registry.get(sub_app_name)
                    path = f"/{sub_app_name}"
                    if sub_app_cls:
                        path = sub_app_cls._get_clean_path()
                    
                    group_items.append({
                        "type": "app_link",
                        "name": sub_app_name,
                        "path": path
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
                    "label": cls._view_label(model_name, m),
                    "path": cls._get_clean_path(model_name),
                    "icon": getattr(m, "__icon__", "FileText")
                })
        
        if standalone_items:
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
            "app_type": cls.app_type,
            "label": cls.app_label,
            "description": cls.description,
            "version": cls.version,
            "icon": cls.icon,
            "have_home": cls.have_home,
            "requires": cls.requires,
            "optional_features": cls.optional_features,
            "models": [m.__tablename__ for m in cls.models if hasattr(m, "__tablename__")],
            "menu_groups": cls.menu_groups
        }

    @classmethod
    def seed(cls, db: Any):
        """Seeds initial data for the app. Subclasses should override this."""
        pass
