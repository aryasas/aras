from typing import Dict, Any, Type, List, Optional
from pydantic import BaseModel

class Aras:
    """
    The ultimate abstract root for the Aras framework.
    Handles automated namespace mapping and generic registration.
    """
    @classmethod
    def get_registered(cls, name: str) -> dict:
        target = getattr(cls, name.capitalize(), None)
        if target is None:
            raise AttributeError(f"Aras has no namespace '{name.capitalize()}'")
        return getattr(target, "_registry", {})

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # 1. Automatic Namespace Attachment (ArasSomething -> Aras.Something)
        if cls.__name__.startswith("Aras") and cls.__name__ != "Aras":
            attr_name = cls.__name__[4:]
            if attr_name:
                setattr(Aras, attr_name, cls)

        # 2. Generic Registration
        # If the direct parent has a _registry, register this class into it
        if not cls.__dict__.get("__abstract__"):
            # We look for _registry in the base classes
            for base in cls.__bases__:
                if hasattr(base, "_registry") and isinstance(getattr(base, "_registry"), dict):
                    # Register the class in the parent's registry
                    base._registry[cls.__name__] = cls

class ArasValidation(Aras, BaseModel):
    """
    Base class for all Aras Pydantic models (schemas/validation).
    """
    __abstract__ = True
    _registry: Dict[str, Type['ArasValidation']] = {}

class ArasApp(Aras):
    """
    Abstract base for application modules (e.g., ERP, CRM).
    """
    __abstract__ = True
    _registry: Dict[str, Type['ArasApp']] = {}

    app_name: str = ""
    app_label: str = ""
    description: str = ""
    version: str = "1.0.0"
    icon: str = "Package"
    models: List[Any] = []

    @classmethod
    def get_manifest(cls):
        return {
            "name": cls.app_name,
            "label": cls.app_label,
            "description": cls.description,
            "version": cls.version,
            "icon": cls.icon,
            "models": [m.__tablename__ for m in cls.models if hasattr(m, "__tablename__")]
        }

# "Connect" components from other modules to the Aras class
from .model import ArasModel, ArasSoftModel, ArasColumn, Base
from .lib.database import SessionLocal, get_db, engine

# Attach non-class utilities
Aras.Column = ArasColumn
Aras.Base = Base
Aras.db = SessionLocal
Aras.get_db = get_db
Aras.engine = engine

# Now import modules that depend on Aras.Model/Column
from .auth.models import User
from .crud import create_aras_router

# Attach remaining components
Aras.User = User
Aras.Router = create_aras_router

# Expose only the Aras class
__all__ = ["Aras"]
