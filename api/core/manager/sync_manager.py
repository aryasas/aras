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
from ..registry.link_model import LinkModel
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
        
        try:
            # 0. Seed Global Settings
            cls.seed_settings(db)

            # Get all apps registered via Level 2 App inheritance
            apps = App._registry
            
            # 1. Sync active apps
            for app_name, app_cls in apps.items():
                print(f"[SyncManager] Syncing app: {app_name}")
                cls.sync_app(db, app_cls)
            
            db.flush() # Ensure all Resources are in DB and have IDs

            # 2. Cleanup/Deactivate stale apps
            registered_app_names = [cls.app_name for cls in apps.values() if hasattr(cls, "app_name")]
            db.query(AppModel).filter(
                ~AppModel.name.in_(registered_app_names)
            ).update({"is_active": False}, synchronize_session=False)

            # 3. Cleanup/Deactivate stale resources within active apps
            registered_resource_names = []
            for app_cls in apps.values():
                registered_resource_names.extend([m.__tablename__ for m in app_cls.models])
            
            db.query(ResourceModel).filter(
                ~ResourceModel.name.in_(registered_resource_names)
            ).update({"is_active": False}, synchronize_session=False)

            print("[SyncManager] Syncing relationships (links)...")
            for app_name, app_cls in apps.items():
                for model_cls in app_cls.models:
                    resource_db = db.query(ResourceModel).filter(
                        ResourceModel.name == model_cls.__tablename__
                    ).first()
                    if resource_db:
                        cls.sync_links(db, resource_db.id, model_cls)
                
            db.commit()
            print("[SyncManager] Synchronization complete.")
        except Exception as e:
            db.rollback()
            print(f"[SyncManager] CRITICAL: Synchronization failed: {str(e)}")
            raise

    @classmethod
    def seed_settings(cls, db: Session):
        """Seeds global framework settings if they don't exist."""
        # Import here to avoid circular dependencies
        try:
            from apps.admin.models import ArasSetting
        except ImportError:
            print("[SyncManager] Warning: apps.admin.models.ArasSetting not found. Skipping settings seed.")
            return

        defaults = [
            ("core.date_format", "YYYY-MM-DD", "Global date format (e.g. YYYY-MM-DD)"),
            ("core.number_format", "#,###.##", "Global number format (e.g. #,###.##)"),
            ("core.decimal_precision", "2", "Default decimal precision for currency/numeric fields"),
            ("core.currency_symbol", "$", "Default currency symbol"),
            ("core.language_default", "en", "Default system language code"),
        ]

        for key, value, desc in defaults:
            row = db.query(ArasSetting).filter(ArasSetting.key == key).first()
            if not row:
                print(f"[SyncManager] Seeding setting: {key} = {value}")
                db.add(ArasSetting(key=key, value=value, description=desc))
        
        db.flush()

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
                version=manifest["version"],
                is_active=True
            )
            db.add(app_db)
            db.flush() # Get ID
        else:
            app_db.label = manifest["label"]
            app_db.description = manifest["description"]
            app_db.icon = manifest["icon"]
            app_db.version = manifest["version"]
            app_db.is_active = True

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
                features=getattr(model_cls, "__features__", []),
                is_active=True
            )
            db.add(resource_db)
            db.flush()
        else:
            resource_db.title = getattr(model_cls, "__title__", table_name.replace("_", " ").title())
            resource_db.features = getattr(model_cls, "__features__", [])
            resource_db.is_active = True

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
                "label": column.info.get("label") or column.name.replace("_", " ").title(),
                "ui_type": column.info.get("ui_type") or "string",
                "is_required": not column.nullable,
                "is_read_only": column.info.get("read_only", False),
                "is_hidden": column.info.get("hidden", False),
                "is_searchable": column.info.get("searchable", True),
                "link_column": column.info.get("link_column"),
                "display_column": column.info.get("display_column")
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

    @classmethod
    def sync_links(cls, db: Session, resource_id: int, model_cls: Type[Model]):
        """Detects and syncs relationships (ForeignKeys and Child Tables)."""
        # 1. Detect Lookups (Foreign Keys)
        for column in model_cls.__table__.columns:
            if column.foreign_keys:
                for fk in column.foreign_keys:
                    target_table = fk.column.table.name
                    target_resource = db.query(ResourceModel).filter(ResourceModel.name == target_table).first()
                    
                    if target_resource:
                        link_db = db.query(LinkModel).filter(
                            LinkModel.source_resource_id == resource_id,
                            LinkModel.target_resource_id == target_resource.id,
                            LinkModel.field_name == column.name
                        ).first()
                        
                        if not link_db:
                            link_db = LinkModel(
                                source_resource_id=resource_id,
                                target_resource_id=target_resource.id,
                                field_name=column.name,
                                link_type="lookup",
                                label=column.info.get("label", column.name.replace("_id", "").replace("_", " ").title()),
                                display_column=column.info.get("display_column")
                            )
                            db.add(link_db)

        # 2. Detect Child Tables (from the perspective of the Parent)
        children = Model._child_map.get(model_cls.__tablename__, [])
        for child_table in children:
            target_resource = db.query(ResourceModel).filter(ResourceModel.name == child_table).first()
            if target_resource:
                link_db = db.query(LinkModel).filter(
                    LinkModel.source_resource_id == resource_id,
                    LinkModel.target_resource_id == target_resource.id,
                    LinkModel.link_type == "child"
                ).first()
                
                if not link_db:
                    link_db = LinkModel(
                        source_resource_id=resource_id,
                        target_resource_id=target_resource.id,
                        field_name="id", # Parent's ID is the anchor
                        link_type="child",
                        label=target_resource.title,
                        show_as_child=True
                    )
                    db.add(link_db)
