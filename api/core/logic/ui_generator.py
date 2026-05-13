"""
Purpose: Centralized utility for automatically generating UI metadata from SQLAlchemy models.
Context: Decouples UI logic from core database models.
"""
from typing import Any, Dict, List
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric
from ..base.service import Service

class UIGenerator(Service):
    """
    Utility class that handles the 'Zero Code' auto-detection 
    of UI components from SQLAlchemy models.
    """

    @classmethod
    def generate_metadata(cls, model_class: Any, db: Any = None, translations: Dict[str, str] = None) -> Dict[str, Any]:
        """Generates metadata for a given model, merging code detection with DB overrides."""
        from ..registry.resource_model import ResourceModel
        from ..registry.field_model import FieldModel

        fields = []
        translations = translations or {}
        table = model_class.__table__
        resource_name = table.name
        
        # 1. Try to fetch DB Overrides if DB session provided
        db_resource = None
        db_fields = {}
        if db:
            db_resource = db.query(ResourceModel).filter(ResourceModel.name == resource_name).first()
            if db_resource:
                field_records = db.query(FieldModel).filter(FieldModel.resource_id == db_resource.id).all()
                db_fields = {f.name: f for f in field_records}

        # 2. Base Metadata from Code
        system_fields = getattr(model_class, "_SYSTEM", set())
        child_map = getattr(model_class, "_child_map", {})
        
        for column in table.columns:
            if column.name in system_fields:
                continue
            
            # DB Override Check
            db_field = db_fields.get(column.name)
            
            # Detect Foreign Key (Lookup)
            target_resource = None
            ui_options = None
            ui_type = column.info.get("ui_type")
            
            if column.foreign_keys:
                target_resource = list(column.foreign_keys)[0].column.table.name
                if not ui_type:
                    ui_type = "lookup"
            
            if not ui_type:
                col_type = column.type
                from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric, Enum
                
                if isinstance(col_type, Enum) or hasattr(col_type, "enums"):
                    ui_type = "select"
                    ui_options = [{"label": str(e), "value": str(e)} for e in getattr(col_type, "enums", [])]
                elif isinstance(col_type, String): ui_type = "string"
                elif isinstance(col_type, (Integer, Numeric)): ui_type = "number"
                elif isinstance(col_type, Boolean): ui_type = "boolean"
                elif isinstance(col_type, DateTime): ui_type = "datetime"
                elif isinstance(col_type, Date): ui_type = "date"
                else: ui_type = "string"

            # Apply DB Overrides if present
            label = db_field.label if db_field and db_field.label else \
                    translations.get(f"field.{column.name}.label") or \
                    column.info.get("label", column.name.replace("_id", "").replace("_", " ").title())
            
            final_ui_type = db_field.ui_type if db_field and db_field.ui_type else ui_type
            is_hidden = db_field.is_hidden if db_field and db_field.is_hidden is not None else column.info.get("hidden", False)
            is_read_only = db_field.is_read_only if db_field and db_field.is_read_only is not None else column.info.get("read_only", False)
            is_searchable = db_field.is_searchable if db_field and db_field.is_searchable is not None else column.info.get("searchable", True)

            # Determine if the field is required for the UI
            is_required = db_field.is_required if db_field and db_field.is_required is not None else \
                          (not column.nullable and column.default is None and column.server_default is None and column.name != 'is_active')

            field_info = {
                "name": column.name,
                "label": label,
                "type": final_ui_type,
                "required": is_required,
                "target_resource": target_resource,
                "options": ui_options,
                "hidden": is_hidden,
                "read_only": is_read_only,
                "searchable": is_searchable,
                "link_column": db_field.link_column if db_field and db_field.link_column else column.info.get("link_column"),
                "display_column": db_field.display_column if db_field and db_field.display_column else column.info.get("display_column")
            }
            fields.append(field_info)

        return {
            "resource": resource_name,
            "title": db_resource.title if db_resource and db_resource.title else \
                     translations.get("resource.title") or \
                     getattr(model_class, "__title__", resource_name.replace("_", " ").title()),
            "fields": fields,
            "children": child_map.get(resource_name, []),
            "workflow": getattr(model_class, "__workflow__", None),
            "is_auditable": "audit" in getattr(model_class, "__features__", [])
        }

