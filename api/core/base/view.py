"""
Purpose: Level 2 Base View class for UI configuration.
Context: Decouples UI metadata from SQLAlchemy models.
Impact: Allows developers to customize forms/lists without changing DB models.
"""
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
            if hasattr(cls, 'model'):
                View._view_map[cls.model.__tablename__] = cls

    model: Type['Aras.Model'] = None
    title: Optional[str] = None
    fields: Dict[str, Dict[str, Any]] = {}
    layout: Optional[list] = None

    @classmethod
    def get_for_model(cls, model_class: Type['Aras.Model']) -> Optional[Type['View']]:
        return cls._view_map.get(model_class.__tablename__)

    @classmethod
    def render_metadata(cls, translations: Dict[str, str] = None) -> Dict[str, Any]:
        """Generates metadata, applying View-level overrides to the generated defaults."""
        metadata = UIGenerator.generate_metadata(cls.model, translations=translations)
        
        # Override with custom view settings
        if cls.title:
            metadata["title"] = cls.title
        
        # Apply field overrides
        if cls.fields:
            for field_meta in metadata["fields"]:
                if field_meta["name"] in cls.fields:
                    field_meta.update(cls.fields[field_meta["name"]])
        
        if cls.layout:
            metadata["layout"] = cls.layout
            
        return metadata
