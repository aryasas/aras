"""
Purpose: Level 2 Base Schema class for custom Pydantic validation.
Context: Decouples validation logic from models and views.
Impact: Allows developers to define complex business rules and API structures.
"""
from typing import Dict, Type, Optional, Any, ClassVar
from .validation import Validation

class Schema(Validation):
    """
    Base Schema class for defining custom Pydantic validation.
    Developers can inherit from this to override auto-generated API schemas.
    """
    __abstract__ = True
    _schema_map: ClassVar[Dict[str, Type['Schema']]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("__abstract__"):
            if hasattr(cls, 'model') and cls.model is not None:
                # Register the schema for the model
                model_name = cls.model if isinstance(cls.model, str) else cls.model.__tablename__
                Schema._schema_map[model_name] = cls

    model: ClassVar[Any] = None # Reference to the Aras.Model (class or tablename)

    @classmethod
    def get_for_model(cls, model_name: str) -> Optional[Type['Schema']]:
        """Returns the custom schema registered for a model tablename."""
        return cls._schema_map.get(model_name)
