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
    def generate_metadata(cls, model_class: Any, translations: Dict[str, str] = None) -> Dict[str, Any]:
        """Generates default metadata for a given model."""
        fields = []
        translations = translations or {}
        
        # We need to access model metadata via __table__
        table = model_class.__table__
        
        # Access class-level properties
        system_fields = getattr(model_class, "_SYSTEM", set())
        child_map = getattr(model_class, "_child_map", {})
        
        for column in table.columns:
            if column.name in system_fields:
                continue
            
            # Detect Foreign Key (Lookup)
            target_resource = None
            ui_type = column.info.get("ui_type")
            
            if column.foreign_keys:
                target_resource = list(column.foreign_keys)[0].column.table.name
                if not ui_type:
                    ui_type = "lookup"
            
            if not ui_type:
                col_type = column.type
                if isinstance(col_type, String): ui_type = "string"
                elif isinstance(col_type, (Integer, Numeric)): ui_type = "number"
                elif isinstance(col_type, Boolean): ui_type = "boolean"
                elif isinstance(col_type, DateTime): ui_type = "datetime"
                elif isinstance(col_type, Date): ui_type = "date"
                else: ui_type = "string"

            # Apply Translation if available
            label = translations.get(f"field.{column.name}.label") or \
                    column.info.get("label", column.name.replace("_id", "").replace("_", " ").title())

            # Determine if the field is required for the UI
            is_required = not column.nullable and column.default is None and column.server_default is None and column.name != 'is_active'

            field_info = {
                "name": column.name,
                "label": label,
                "type": ui_type,
                "required": is_required,
                "target": target_resource,
                "hidden": column.info.get("hidden", False)
            }
            fields.append(field_info)

        return {
            "resource": table.name,
            "title": translations.get("resource.title") or \
                     getattr(model_class, "__title__", table.name.replace("_", " ").title()),
            "fields": fields,
            "children": child_map.get(table.name, []),
            "workflow": getattr(model_class, "__workflow__", None),
        }
