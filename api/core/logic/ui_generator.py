"""
Purpose: Centralized utility for automatically generating UI metadata from SQLAlchemy models.
Context: Decouples UI logic from core database models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric
from ..base.service import Service
from ..lib.i18n import TranslationService # Import TranslationService

class UIGenerator(Service):
    """
    Utility class that handles the 'Zero Code' auto-detection 
    of UI components from SQLAlchemy models.
    """

    @classmethod
    def generate_metadata(cls, model_class: Any, db: Any = None, lang: Optional[str] = None) -> Dict[str, Any]: # Changed translations to lang
        """Generates metadata for a given model, merging code detection with DB overrides."""
        from ..registry.resource_model import ResourceModel
        from ..registry.field_model import FieldModel

        fields = []
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

            # 3. Auto-detect Files/Images by Name
            if not column.info.get("ui_type") and ui_type == "string":
                if any(suffix in column.name for suffix in ["_file", "_path", "_attachment"]):
                    ui_type = "file"
                elif any(suffix in column.name for suffix in ["_image", "_photo", "_avatar"]):
                    ui_type = "image"

            # Apply DB Overrides if present
            # Removed direct translation logic here, will be handled by TranslationService
            label = db_field.label if db_field and db_field.label else \
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
                "label": label, # Label is still raw here, will be translated later
                "type": final_ui_type,
                "required": is_required,
                "target_resource": target_resource,
                "options": ui_options,
                "hidden": is_hidden,
                "read_only": is_read_only,
                "searchable": is_searchable,
                "depends_on": column.info.get("depends_on"),
                "link_column": db_field.link_column if db_field and db_field.link_column else column.info.get("link_column"),
                "display_column": db_field.display_column if db_field and db_field.display_column else column.info.get("display_column")
            }
            fields.append(field_info)

        # 4. Include Many-to-Many (Bridge) Fields
        if db and db_resource:
            from ..registry.link_model import LinkModel
            from ..registry.resource_model import ResourceModel
            bridge_links = db.query(LinkModel).filter(
                LinkModel.source_resource_id == db_resource.id,
                LinkModel.link_type == "bridge"
            ).all()
            for link in bridge_links:
                target_res = db.query(ResourceModel).filter(ResourceModel.id == link.target_resource_id).first()
                if target_res:
                    fields.append({
                        "name": link.field_name,
                        "label": link.label,
                        "type": "bridge",
                        "required": False,
                        "target_resource": target_res.name,
                        "options": None,
                        "hidden": False,
                        "read_only": False,
                        "searchable": False,
                        "depends_on": None,
                        "config": link.config
                    })
        else:
            # Fallback to code definition if DB not synced yet
            m2m_defs = getattr(model_class, "__m2m__", {})
            for field_name, defs in m2m_defs.items():
                fields.append({
                    "name": field_name,
                    "label": defs.get("label", field_name.replace("_", " ").title()),
                    "type": "bridge",
                    "required": False,
                    "target_resource": defs.get("target_resource"),
                    "options": None,
                    "hidden": False,
                    "read_only": False,
                    "searchable": False,
                    "depends_on": None,
                    "config": defs
                })

        # 5. Include Computed Fields
        for name in getattr(model_class, "_computed", []):
            label = name.replace("_", " ").title()
            fields.append({
                "name": name,
                "label": label,
                "type": "string", # Default for computed
                "required": False,
                "target_resource": None,
                "options": None,
                "hidden": False,
                "read_only": True,
                "searchable": False,
                "depends_on": None,
                "is_computed": True
            })

        metadata = {
            "resource": resource_name,
            "title": db_resource.title if db_resource and db_resource.title else \
                     getattr(model_class, "__title__", resource_name.replace("_", " ").title()),
            "fields": fields,
            "children": child_map.get(resource_name, []),
            "workflow": getattr(model_class, "__workflow__", None),
            "layout": getattr(model_class, "__layout__", None),
            "is_auditable": "audit" in getattr(model_class, "__features__", [])
        }

        # 4. Apply Translations if lang is provided
        if lang and db:
            metadata = TranslationService.translate_metadata_dict(metadata, lang, db)
        
        # 5. Add Custom Model Actions Metadata
        actions_metadata = []
        for action_name, model_action in model_class._actions.items():
            actions_metadata.append({
                "name": model_action.name,
                "label": model_action.label,
                "permission": model_action.permission,
                "icon": model_action.icon,
                "has_input_schema": model_action.input_schema is not None
            })
        metadata["actions"] = actions_metadata
            
        return metadata

