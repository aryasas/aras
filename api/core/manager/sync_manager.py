"""
Purpose: Logic for synchronizing Python-defined metadata to the Database Registry.
Context: Level 3 Implementation. Inherits from Manager (Level 2).
Impact: Ensures the DB inventory (Apps, Resources, Fields) is always up-to-date with code.
"""
from typing import List, Type
from sqlalchemy.orm import Session
from ..base.app import App
from ..base.model import Model
from ..registry.app_model import AppModel
from ..registry.resource_model import ResourceModel
from ..registry.field_model import FieldModel
from .manager import Manager

class SyncManager(Manager):
    """
    Orchestrates the Code-to-DB Synchronization process.
    - Scans registered App classes.
    - Upserts App, Resource, and Field records.
    - Preserves GUI overrides.
    """

    @classmethod
    def sync_all(cls, db: Session):
        """
        Main entry point for framework synchronization.
        Iterates through Aras.App._registry and syncs each app.
        """
        print("[SyncManager] Starting metadata synchronization...")
        
        # Get all apps registered via Level 2 App inheritance
        apps = App._registry
        
        for app_name, app_cls in apps.items():
            cls.sync_app(db, app_cls)
            
        db.commit()
        print("[SyncManager] Synchronization complete.")

    @classmethod
    def sync_app(cls, db: Session, app_cls: Type[App]):
        """Syncs a single App manifest and its associated models."""
        manifest = app_cls.get_manifest()
        
        # 1. Upsert App Record
        app_db = db.query(AppModel).filter(AppModel.name == manifest["name"]).first()
        if not app_db:
            app_db = AppModel(
                name=manifest["name"],
                label=manifest["label"],
                description=manifest["description"],
                icon=manifest["icon"],
                version=manifest["version"]
            )
            db.add(app_db)
            db.flush() # Get ID
        else:
            app_db.label = manifest["label"]
            app_db.description = manifest["description"]
            app_db.icon = manifest["icon"]
            app_db.version = manifest["version"]

        # 2. Sync Models (Resources)
        for model_cls in app_cls.models:
            cls.sync_resource(db, app_db.id, model_cls)

    @classmethod
    def sync_resource(cls, db: Session, app_id: int, model_cls: Type[Model]):
        """Syncs a Model class to the ResourceRegistry and syncs its fields."""
        table_name = model_cls.__tablename__
        
        resource_db = db.query(ResourceModel).filter(ResourceModel.name == table_name).first()
        
        if not resource_db:
            resource_db = ResourceModel(
                app_id=app_id,
                name=table_name,
                title=getattr(model_cls, "__title__", table_name.replace("_", " ").title()),
                model_class=model_cls.__name__,
                features=getattr(model_cls, "__features__", [])
            )
            db.add(resource_db)
            db.flush()
        else:
            resource_db.title = getattr(model_cls, "__title__", table_name.replace("_", " ").title())
            resource_db.features = getattr(model_cls, "__features__", [])

        # 3. Sync Fields
        cls.sync_fields(db, resource_db.id, model_cls)

    @classmethod
    def sync_fields(cls, db: Session, resource_id: int, model_cls: Type[Model]):
        """Syncs all columns of a model to the FieldRegistry, preserving GUI overrides."""
        for column in model_cls.__table__.columns:
            # Skip internal system fields
            if column.name in model_cls._SYSTEM:
                continue
                
            field_db = db.query(FieldModel).filter(
                FieldModel.resource_id == resource_id,
                FieldModel.name == column.name
            ).first()

            # Metadata from code
            code_meta = {
                "label": column.info.get("label", column.name.replace("_", " ").title()),
                "ui_type": column.info.get("ui_type", "string"),
                "is_required": not column.nullable,
                "is_read_only": column.info.get("read_only", False),
                "is_hidden": column.info.get("hidden", False),
                "is_searchable": column.info.get("searchable", True)
            }

            if not field_db:
                field_db = FieldModel(
                    resource_id=resource_id,
                    name=column.name,
                    **code_meta
                )
                db.add(field_db)
            elif not field_db.is_override:
                # Update only if not overridden via GUI
                for key, val in code_meta.items():
                    setattr(field_db, key, val)
