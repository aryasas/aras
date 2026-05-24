"""
Purpose: Logic for synchronizing Python-defined metadata to the Database Registry.
Context: Level 3 Implementation. Inherits from Manager (Level 2).
Impact: Ensures the DB inventory (Apps, Resources, Fields) is always up-to-date with code.
"""
import logging
from typing import List, Type
from sqlalchemy.orm import Session
from ..base.app import App
from ..base.model import Model
from ..registry.app_model import AppModel
from ..registry.resource_model import ResourceModel
from ..registry.field_model import FieldModel
from ..registry.link_model import LinkModel
from .manager import Manager
from ..logic import auto_migrate

logger = logging.getLogger(__name__)

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
        logger.info("Starting metadata synchronization...")
        
        try:
            # 0. Seed Global Settings
            cls.seed_settings(db)

            # 0.1 Seed Default Widgets
            cls.seed_widgets(db)

            # Get all apps registered via Level 2 App inheritance
            apps = App._registry
            
            # 1. Sync active apps
            for app_name, app_cls in apps.items():
                logger.info(f"Syncing app: {app_name}")
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

            logger.info("Syncing relationships (links)...")
            for app_name, app_cls in apps.items():
                for model_cls in app_cls.models:
                    resource_db = db.query(ResourceModel).filter(
                        ResourceModel.name == model_cls.__tablename__
                    ).first()
                    if resource_db:
                        cls.sync_links(db, resource_db.id, model_cls)
            
            db.commit()

            # 4. Trigger Auto-Migration to ensure physical tables match models
            logger.info("Running auto-migration...")
            from ..aras import Aras
            report = auto_migrate.run(Aras.engine, Aras.Base.metadata)
            if report.errors:
                logger.error(f"Auto-migration encountered errors: {report.errors}")
            
            logger.info("Synchronization complete.")
        except Exception as e:
            db.rollback()
            logger.error(f"CRITICAL: Synchronization failed: {str(e)}")
            raise

    @classmethod
    def seed_settings(cls, db: Session):
        """Seeds global framework settings if they don't exist."""
        # Import here to avoid circular dependencies
        try:
            from core.registry.sys_settings import ArasSetting
        except ImportError:
            logger.warning("core.registry.sys_settings.ArasSetting not found. Skipping settings seed.")
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
                logger.info(f"Seeding setting: {key} = {value}")
                db.add(ArasSetting(key=key, value=value, description=desc))
        
        db.flush()

    @classmethod
    def seed_widgets(cls, db: Session):
        """Seeds default dashboard widgets."""
        try:
            from core.registry.widget_model import WidgetModel
        except ImportError:
            return

        defaults = [
            {
                "name": "total_products",
                "title": "Total Products",
                "widget_type": "stat",
                "resource_name": "erp_stock_products",
                "config_json": {"icon": "Package", "color": "indigo"},
                "size": "col-span-1",
                "order": 1
            },
            {
                "name": "recent_movements",
                "title": "Recent Stock Movements",
                "widget_type": "list",
                "resource_name": "erp_stock_movements",
                "config_json": {"limit": 5},
                "size": "col-span-2",
                "order": 2
            },
            {
                "name": "total_accounts",
                "title": "Total Accounts",
                "widget_type": "stat",
                "resource_name": "erp_accounting_accounts",
                "config_json": {"icon": "Calculator", "color": "emerald"},
                "size": "col-span-1",
                "order": 3
            },
            {
                "name": "recent_entries",
                "title": "Recent Journal Entries",
                "widget_type": "list",
                "resource_name": "erp_accounting_entries",
                "config_json": {"limit": 5},
                "size": "col-span-2",
                "order": 4
            },
            {
                "name": "total_customers",
                "title": "Total Customers",
                "widget_type": "stat",
                "resource_name": "erp_party_parties",
                "config_json": {"icon": "Users", "color": "indigo"},
                "size": "col-span-1",
                "order": 5
            }
        ]

        for w in defaults:
            row = db.query(WidgetModel).filter(WidgetModel.name == w["name"]).first()
            if not row:
                logger.info(f"Seeding widget: {w['name']}")
                db.add(WidgetModel(**w))
        
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
                parent_name=manifest.get("parent_name"),
                app_type=manifest.get("app_type", "app"),
                label=manifest["label"],
                description=manifest["description"],
                icon=manifest["icon"],
                version=manifest["version"],
                menu_groups=manifest.get("menu_groups", []),
                requires=manifest.get("requires", []),
                optional_features=manifest.get("optional_features", {}),
                is_active=True
            )
            db.add(app_db)
            db.flush() # Get ID
        else:
            app_db.parent_name = manifest.get("parent_name")
            app_db.app_type = manifest.get("app_type", "app")
            app_db.label = manifest["label"]
            app_db.description = manifest["description"]
            app_db.icon = manifest["icon"]
            app_db.version = manifest["version"]
            app_db.menu_groups = manifest.get("menu_groups", [])
            app_db.requires = manifest.get("requires", [])
            app_db.optional_features = manifest.get("optional_features", {})
            app_db.is_active = True

        # 2. Sync Models (Resources)
        for model_cls in app_cls.models:
            cls.sync_resource(db, app_db.id, model_cls)

    @classmethod
    def sync_resource(cls, db: Session, app_id: int, model_cls: Type[Model]):
        """Syncs a Model class to the ResourceRegistry and syncs its fields."""
        from ..aras import Aras
        table_name = model_cls.__tablename__
        
        # Determine Title, Icon and Layout from View or Model
        view = Aras.View.get_for_model(model_cls)
        title = getattr(view, "title", None) or getattr(model_cls, "__title__", None) or table_name.replace("_", " ").title()
        icon = getattr(view, "icon", None)
        layout = getattr(view, "layout", None) or []

        resource_db = db.query(ResourceModel).filter(ResourceModel.name == table_name).first()
        
        scoped_by = [list(p) for p in (getattr(model_cls, "__scoped_by__", None) or [])]
        if not resource_db:
            resource_db = ResourceModel(
                app_id=app_id,
                name=table_name,
                title=title,
                model_class=model_cls.__name__,
                features=getattr(model_cls, "__features__", []),
                scoped_by=scoped_by,
                layout=layout,
                is_active=True
            )
            db.add(resource_db)
            db.flush()
        else:
            resource_db.title = title
            resource_db.features = getattr(model_cls, "__features__", [])
            resource_db.scoped_by = scoped_by
            resource_db.layout = layout
            resource_db.is_active = True

        # 3. Sync Fields
        cls.sync_fields(db, resource_db.id, model_cls)

    @classmethod
    def sync_fields(cls, db: Session, resource_id: int, model_cls: Type[Model]):
        """Syncs all columns of a model to the FieldRegistry, prioritizing View metadata."""
        from ..aras import Aras
        from ..logic.ui_generator import UIGenerator

        # Get Metadata (Prioritize View, Fallback to Auto)
        view = Aras.View.get_for_model(model_cls)
        if view:
            metadata = view.render_metadata()
        else:
            metadata = UIGenerator.generate_metadata(model_cls)

        field_meta_map = {f["name"]: f for f in metadata.get("fields", [])}

        for column in model_cls.__table__.columns:
            # Skip internal system fields
            if column.name in model_cls._SYSTEM:
                continue
                
            field_db = db.query(FieldModel).filter(
                FieldModel.resource_id == resource_id,
                FieldModel.name == column.name
            ).first()

            # Metadata from View/Generator
            meta = field_meta_map.get(column.name, {})
            code_meta = {
                "label": meta.get("label") or column.name.replace("_", " ").title(),
                "ui_type": meta.get("type") or "string",
                "is_required": meta.get("required", not column.nullable),
                "is_read_only": meta.get("read_only", column.info.get("read_only", False)),
                "is_hidden": meta.get("hidden", column.info.get("hidden", False)),
                "is_list_hidden": meta.get("list_hidden", column.info.get("list_hidden", False)),
                "is_searchable": meta.get("searchable", column.info.get("searchable", True)),
                "link_column": meta.get("link_column", column.info.get("link_column")),
                "display_column": meta.get("display_column", column.info.get("display_column"))
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

        # 2. Detect Many-to-Many (Bridge)
        m2m_defs = getattr(model_cls, "__m2m__", {})
        for field_name, defs in m2m_defs.items():
            target_table = defs.get("target_resource")
            target_resource = db.query(ResourceModel).filter(ResourceModel.name == target_table).first()
            if target_resource:
                link_db = db.query(LinkModel).filter(
                    LinkModel.source_resource_id == resource_id,
                    LinkModel.target_resource_id == target_resource.id,
                    LinkModel.field_name == field_name,
                    LinkModel.link_type == "bridge"
                ).first()
                
                if not link_db:
                    link_db = LinkModel(
                        source_resource_id=resource_id,
                        target_resource_id=target_resource.id,
                        field_name=field_name,
                        link_type="bridge",
                        label=defs.get("label", field_name.replace("_", " ").title()),
                        config=defs
                    )
                    db.add(link_db)

        # 3. Detect Child Tables (from the perspective of the Parent)
        children = Model._child_map.get(model_cls.__tablename__, [])
        for child_entry in children:
            child_table = child_entry.get("resource") if isinstance(child_entry, dict) else child_entry
            if not child_table:
                continue
            target_resource = db.query(ResourceModel).filter(ResourceModel.name == child_table).first()
            if target_resource:
                # Try to find the relationship name on the parent model
                from sqlalchemy import inspect
                relationship_name = child_table # Fallback
                try:
                    mapper = inspect(model_cls)
                    for rel in mapper.relationships:
                        if hasattr(rel.mapper.class_, "__tablename__") and rel.mapper.class_.__tablename__ == child_table:
                            relationship_name = rel.key
                            break
                except Exception:
                    pass

                link_db = db.query(LinkModel).filter(
                    LinkModel.source_resource_id == resource_id,
                    LinkModel.target_resource_id == target_resource.id,
                    LinkModel.link_type == "child"
                ).first()
                
                if not link_db:
                    link_db = LinkModel(
                        source_resource_id=resource_id,
                        target_resource_id=target_resource.id,
                        field_name=relationship_name,
                        link_type="child",
                        label=target_resource.title,
                        show_as_child=True
                    )
                    db.add(link_db)
                else:
                    # Update field_name if it changed or was "id"
                    if link_db.field_name != relationship_name:
                        link_db.field_name = relationship_name
