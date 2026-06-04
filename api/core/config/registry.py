# claude-sonnet-4-6
"""
AppConfigRegistry — key-addressed lookup of app config models.

The load-bearing piece of the framework→app decoupling: apps register their
AppConfig subclass at install time (via App.config_model); the framework reads
any app's config by app_name, never importing the app. Absent app → get()
returns None, so a free plan that lacks accounting simply has no accounting
config, no crash. Same inversion as the existing ServiceRegistry.
"""
from typing import Dict, Optional, Type
from sqlalchemy.orm import Session
from .app_config import AppConfig


class AppConfigRegistry:
    _models: Dict[str, Type[AppConfig]] = {}

    @classmethod
    def register(cls, app_name: str, model: Type[AppConfig]) -> None:
        cls._models[app_name] = model

    @classmethod
    def model_for(cls, app_name: str) -> Optional[Type[AppConfig]]:
        return cls._models.get(app_name)

    @classmethod
    def get(cls, db: Session, app_name: str, org_id: int) -> Optional[AppConfig]:
        """Return the app's config row for an org, or None if the app provides
        no config model (e.g. not installed). Never raises on absence."""
        model = cls._models.get(app_name)
        if model is None:
            return None
        return db.query(model).filter_by(org_id=org_id).first()

    @classmethod
    def get_or_create(cls, db: Session, app_name: str, org_id: int) -> Optional[AppConfig]:
        """Fetch-or-create the singleton config row for an org. None if no model."""
        model = cls._models.get(app_name)
        if model is None:
            return None
        row = db.query(model).filter_by(org_id=org_id).first()
        if row is None:
            row = model(org_id=org_id)
            db.add(row)
            db.flush()
        return row

    @classmethod
    def all(cls) -> Dict[str, Type[AppConfig]]:
        return dict(cls._models)

    @classmethod
    def clear(cls) -> None:
        cls._models = {}


app_config_registry = AppConfigRegistry()
