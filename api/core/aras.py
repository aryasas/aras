from typing import Dict, Any, Type, List, Optional

class Aras:
    """
    The ultimate abstract base and namespace for all Aras components.
    Handles registration and serves as a container for core framework classes.
    """
    _registry: Dict[str, Dict[str, Type['Aras']]] = {
        "models": {},
        "apps": {},
        "forms": {},
        "services": {}
    }

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # Don't register abstract base classes
        if cls.__dict__.get("__abstract__"):
            return

        # Simple registration based on class names or specific attributes
        if hasattr(cls, "__tablename__"):
            cls._registry["models"][cls.__name__] = cls
        elif cls.__name__.endswith("App") or hasattr(cls, "manifest"):
            cls._registry["apps"][cls.__name__] = cls

    @classmethod
    def get_registered(cls, category: str) -> Dict[str, Type['Aras']]:
        return cls._registry.get(category, {})

    # Framework components will be attached below after their definitions
    App: Any = None
    Model: Any = None
    SoftModel: Any = None
    Column: Any = None
    Base: Any = None
    User: Any = None
    Router: Any = None
    db: Any = None
    get_db: Any = None
    engine: Any = None

class ArasApp(Aras):
    """
    Abstract base for application modules (e.g., ERP, CRM).
    """
    __abstract__ = True

    app_name: str = ""
    app_label: str = ""
    description: str = ""
    version: str = "1.0.0"
    icon: str = "Package"

    # List of model classes for this app
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

# Attach core components first so they are available to other modules
Aras.App = ArasApp
Aras.Model = ArasModel
Aras.SoftModel = ArasSoftModel
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
