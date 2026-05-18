"""
Purpose: Level 2 Base View class for UI configuration.
Context: Decouples UI metadata from SQLAlchemy models.
Impact: Allows developers to customize forms/lists without changing DB models.
"""
import copy
import re
from typing import Dict, Any, Type, Optional
from .aras import Aras
from ..logic.ui_generator import UIGenerator

class View(Aras):
    """
    Base View class for defining UI metadata.
    Developers can inherit from this to override auto-generated defaults.
    """
    __abstract__ = True
    _view_map: Dict[str, Type['View']] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("__abstract__"):
            if hasattr(cls, 'model') and cls.model is not None:
                View._view_map[cls.model.__tablename__] = cls
                # Auto-derive title from model class name if not explicitly set on this subclass
                if not cls.__dict__.get("title"):
                    name = cls.model.__name__
                    for suffix in ("Model", "View"):
                        if name.endswith(suffix):
                            name = name[:-len(suffix)]
                            break
                    cls.title = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', name)

    @classmethod
    def _auto_register(cls, model_class: Type) -> Type['View']:
        """Ensure a model has a View entry, creating a minimal auto-View if needed."""
        tablename = model_class.__tablename__
        if tablename not in cls._view_map:
            type(f"{model_class.__name__}View", (cls,), {"model": model_class})
        return cls._view_map[tablename]

    model: Type['Aras.Model'] = None
    title: Optional[str] = None
    icon: Optional[str] = None
    standalone: bool = False  # child models with standalone=True appear in app menu
    fields: Dict[str, Dict[str, Any]] = {}
    layout: Optional[list] = None

    @classmethod
    def get_for_model(cls, model_class: Type['Aras.Model']) -> Optional[Type['View']]:
        return cls._view_map.get(model_class.__tablename__)

    @classmethod
    def render_metadata(cls, db: Any = None, lang: Optional[str] = None) -> Dict[str, Any]:
        """Generates metadata, applying View-level overrides to the generated defaults."""
        metadata = UIGenerator.generate_metadata(cls.model, db=db, lang=lang)

        # Override with custom view settings
        if cls.title:
            metadata["title"] = cls.title
        if cls.icon:
            metadata["icon"] = cls.icon
        
        # Apply field overrides
        if cls.fields:
            for field_meta in metadata["fields"]:
                if field_meta["name"] in cls.fields:
                    field_meta.update(cls.fields[field_meta["name"]])
        
        if cls.layout:
            layout = copy.deepcopy(cls.layout)
            # Inject scope fields (e.g. org_id) into the first section if missing from all sections
            scoped_by = getattr(cls.model, "__scoped_by__", None) or []
            scope_field_names = [pair[0] for pair in scoped_by]
            if scope_field_names:
                def _section_fields(s):
                    direct = s.get("fields", [])
                    from_tabs = [f for tab in s.get("tabs", []) for f in tab.get("fields", [])]
                    return direct + from_tabs
                def _field_name(f):
                    return f if isinstance(f, str) else f.get("field", "")
                all_layout_fields = {_field_name(f) for s in layout for f in _section_fields(s)}
                missing = [sf for sf in scope_field_names if sf not in all_layout_fields]
                if missing and layout and "fields" in layout[0]:
                    layout[0]["fields"] = missing + list(layout[0]["fields"])
            metadata["layout"] = layout

        return metadata
