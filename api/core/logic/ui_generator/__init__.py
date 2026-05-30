"""
Purpose: Centralized utility for automatically generating UI metadata from SQLAlchemy models.
Context: Decouples UI logic from core database models.
"""
from typing import Any, Dict, List, Optional
from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric
from ...base.service import Service
from ...lib.i18n import TranslationService # Import TranslationService
from ...lib.helpers import to_label_case
from .registry import get_handlers
from .handlers import standard # noqa

class UIGenerator(Service):
    """
    Utility class that handles the 'Zero Code' auto-detection 
    of UI components from SQLAlchemy models.
    """
    _metadata_cache = {}

    @classmethod
    def flush_cache(cls):
        """Clears the metadata cache."""
        cls._metadata_cache = {}

    @classmethod
    def invalidate(cls, resource_name: str):
        """Invalidates all cache entries for a specific resource."""
        keys_to_delete = [k for k in cls._metadata_cache.keys() if k[0] == resource_name]
        for k in keys_to_delete:
            del cls._metadata_cache[k]

    @staticmethod
    def _detect_ui_type(column: Any) -> tuple[str, Optional[list]]:
        """Detects UI type and options for a given SQLAlchemy column."""
        ui_type = column.info.get("ui_type")
        if ui_type:
            return ui_type, None

        handlers = get_handlers()
        # Priority handlers first
        for name in ["lookup", "select", "file_image", "scalar"]:
            handler = handlers.get(name)
            if handler:
                result = handler(column)
                if result:
                    return result
        
        # Fallback to other registered handlers
        for name, handler in handlers.items():
            if name in ["lookup", "select", "file_image", "scalar"]:
                continue
            result = handler(column)
            if result:
                return result
            
        return "string", None

    @classmethod
    def generate_metadata(cls, model_class: Any, db: Any = None, lang: Optional[str] = None, org_id: Optional[int] = None) -> Dict[str, Any]:
        """Generates metadata for a given model, merging code detection with DB overrides."""
        resource_name = model_class.__table__.name
        cache_key = (resource_name, lang or "default", org_id, bool(db))
        
        if cache_key in cls._metadata_cache:
            return cls._metadata_cache[cache_key]

        from ...registry.resource_model import ResourceModel
        from ...registry.field_model import FieldModel

        fields = []
        table = model_class.__table__
        
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
        # children: list of {resource, fk_column}
        children = [dict(c) for c in child_map.get(resource_name, [])]
        
        from ...aras import Aras
        for column in model_class.get_ui_fields():
            # DB Override Check
            db_field = db_fields.get(column.name)
            
            # 2. Base Metadata from Code
            ui_type, ui_options = cls._detect_ui_type(column)
            target_resource = None
            
            if ui_type == "lookup":
                target_table = list(column.foreign_keys)[0].column.table.name
                # Resolve app path for the target resource using ServiceRegistry
                from ...service_registry import ServiceRegistry
                target_resource = ServiceRegistry.get_resource_path(target_table) or target_table

            # Apply DB Overrides if present
            # Removed direct translation logic here, will be handled by TranslationService
            label = db_field.label if db_field and db_field.label else \
                    column.info.get("label", to_label_case(column.name.replace("_id", "")))
            
            final_ui_type = db_field.ui_type if db_field and db_field.ui_type else ui_type
            is_hidden = db_field.is_hidden if db_field and db_field.is_hidden is not None else column.info.get("hidden", False)
            is_list_hidden = db_field.is_list_hidden if db_field and hasattr(db_field, "is_list_hidden") and db_field.is_list_hidden is not None else \
                             column.info.get("list_hidden", False)
            is_read_only = db_field.is_read_only if db_field and db_field.is_read_only is not None else column.info.get("read_only", False)
            is_searchable = db_field.is_searchable if db_field and db_field.is_searchable is not None else column.info.get("searchable", True)

            # Heuristic for default list visibility
            if not is_list_hidden and not (db_field and db_field.is_override):
                if final_ui_type in ["textarea", "file", "image", "json", "object"]:
                    is_list_hidden = True
                elif any(s in column.name for s in ["notes", "description", "comment", "content", "remark"]):
                    is_list_hidden = True

            # Determine if the field is required for the UI
            is_required = db_field.is_required if db_field and db_field.is_required is not None else \
                          (not column.nullable and column.default is None and column.server_default is None)

            form_hidden = bool(column.info.get("form_hidden", False))

            field_info = {
                "name": column.name,
                "label": label, # Label is still raw here, will be translated later
                "type": final_ui_type,
                "required": is_required,
                "target_resource": target_resource,
                "options": ui_options,
                "hidden": is_hidden,
                "list_hidden": is_list_hidden,
                "read_only": is_read_only,
                "searchable": is_searchable,
                "form_hidden": form_hidden,
                "depends_on": column.info.get("depends_on"),
                "default_from": column.info.get("default_from"),
                "default_value": db_field.default_value if db_field else None,
                "series": db_field.series if db_field else None,
                "link_column": db_field.link_column if db_field and db_field.link_column else column.info.get("link_column"),
                "display_column": db_field.display_column if db_field and db_field.display_column else column.info.get("display_column"),
                "fk_filter": column.info.get("fk_filter"),
                "fk_filter_fallback": column.info.get("fk_filter_fallback"),
                "tab": db_field.tab if db_field and db_field.tab else column.info.get("tab"),
                "section": db_field.section if db_field and db_field.section else column.info.get("section"),
                "foldable": db_field.foldable if db_field and db_field.foldable is not None else column.info.get("foldable", False),
                "default_folded": db_field.default_folded if db_field and db_field.default_folded is not None else column.info.get("default_folded", False),
                # claude-opus-4-7
                "display_order": getattr(db_field, "display_order", 0) if db_field else 0,
            }
            fields.append(field_info)

        # claude-opus-4-7
        # Stable sort by display_order; 0 (unset) keeps original column order via Python sort stability.
        if any(f.get("display_order") for f in fields):
            fields.sort(key=lambda f: (f.get("display_order") or 9999))

        # Helper: resolve REST API path for any table name
        from ...service_registry import ServiceRegistry
        def resolve_api_path(tablename: str) -> Optional[str]:
            return ServiceRegistry.get_resource_path(tablename)

        # 4. Include Many-to-Many (Bridge) and Child Table Fields
        if db and db_resource:
            from ...registry.link_model import LinkModel
            from ...registry.resource_model import ResourceModel
            
            # Bridge Links
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
                        "list_hidden": True,
                        "read_only": False,
                        "searchable": False,
                        "depends_on": None,
                        "config": link.config
                    })

            # Child Table Links
            child_links = db.query(LinkModel).filter(
                LinkModel.source_resource_id == db_resource.id,
                LinkModel.link_type == "child"
            ).all()
            db_linked_children = set()
            for link in child_links:
                target_res = db.query(ResourceModel).filter(ResourceModel.id == link.target_resource_id).first()
                if target_res:
                    db_linked_children.add(target_res.name)
                    code_entry = next(
                        (c for c in child_map.get(resource_name, []) if c.get("resource") == target_res.name),
                        None,
                    )
                    fk_col = (code_entry or {}).get("fk_column")
                    if not any(c.get("resource") == target_res.name for c in children):
                        children.append({
                            "resource": target_res.name,
                            "fk_column": fk_col,
                        })
                    fields.append({
                        "name": link.field_name,
                        "label": link.label,
                        "type": "child_table",
                        "required": False,
                        "target_resource": target_res.name,
                        "target_api_path": resolve_api_path(target_res.name),
                        "fk_column": fk_col,
                        "options": None,
                        "hidden": False,
                        "list_hidden": True,
                        "read_only": False,
                        "searchable": False,
                        "depends_on": None,
                        "config": link.config
                    })

            # Also add code-defined children not yet in DB links
            for child_entry in child_map.get(resource_name, []):
                child_table = child_entry.get("resource")
                if child_table and child_table not in db_linked_children:
                    if not any(c.get("resource") == child_table for c in children):
                        children.append(child_entry)
                    from ...aras import Aras
                    fields.append({
                        "name": child_table,
                        "label": to_label_case(child_table),
                        "type": "child_table",
                        "required": False,
                        "target_resource": child_table,
                        "target_api_path": resolve_api_path(child_table),
                        "fk_column": child_entry.get("fk_column"),
                        "options": None,
                        "hidden": False,
                        "list_hidden": True,
                        "read_only": False,
                        "searchable": False,
                        "depends_on": None,
                        "config": None
                    })
        else:
            # Fallback to code definition if DB not synced yet
            m2m_defs = getattr(model_class, "__m2m__", {})
            for field_name, defs in m2m_defs.items():
                from ...aras import Aras
                fields.append({
                    "name": field_name,
                    "label": defs.get("label", to_label_case(field_name)),
                    "type": "bridge",
                    "required": False,
                    "target_resource": defs.get("target_resource"),
                    "options": None,
                    "hidden": False,
                    "list_hidden": True,
                    "read_only": False,
                    "searchable": False,
                    "depends_on": None,
                    "config": defs
                })
            
            # Fallback for children
            for child_entry in child_map.get(resource_name, []):
                child_table = child_entry.get("resource")
                fields.append({
                    "name": child_table,
                    "label": to_label_case(child_table),
                    "type": "child_table",
                    "required": False,
                    "target_resource": child_table,
                    "fk_column": child_entry.get("fk_column"),
                    "options": None,
                    "hidden": False,
                    "list_hidden": True,
                    "read_only": False,
                    "searchable": False
                })

        # 5. Include Computed Fields
        for name in getattr(model_class, "_computed", []):
            label = to_label_case(name)

            fields.append({
                "name": name,
                "label": label,
                "type": "string", # Default for computed
                "required": False,
                "target_resource": None,
                "options": None,
                "hidden": False,
                "list_hidden": False,
                "read_only": True, # Already true
                "searchable": False,
                "depends_on": None,
                "computed": True # Changed from is_computed
            })

        # Find the app for this model to use its clean label logic
        from ...base.app import App as _App
        app_cls = None
        for a in _App._registry.values():
            if model_class in a.models:
                app_cls = a
                break

        def clean_label(name):
            if app_cls:
                return app_cls._get_clean_label(name)
            return to_label_case(name)

        api_path = resolve_api_path(resource_name)

        metadata = {
            "resource": resource_name,
            "api_path": api_path,
            "title": db_resource.title if db_resource and db_resource.title else \
                     getattr(model_class, "__title__", clean_label(resource_name)),
            "fields": fields,
            "children": children,
            "workflow": getattr(model_class, "__workflow__", None),
            "layout": db_resource.layout if db_resource and db_resource.layout else [],
            "is_auditable": "audit" in getattr(model_class, "__features__", []),
            "is_document": "series" in getattr(model_class, "__features__", []),
            "scoped_by": [list(p) for p in (getattr(model_class, "__scoped_by__", None) or [])],
            "list_tabs": getattr(model_class, "__list_tabs__", None) or [],
        }

        # 4. Apply Translations if lang is provided
        if lang and db:
            metadata = TranslationService.translate_metadata_dict(metadata, lang, db)
        
        # 5. Add Custom Model Actions Metadata
        actions_metadata = []
        for action_name, model_action in model_class._actions.items():
            schema_fields = None
            if model_action.input_schema is not None:
                from ...aras import Aras
                schema_fields = [
                    {
                        "name": fname,
                        "label": to_label_case(fname),
                        "required": info.is_required(),
                        "type": _pydantic_type_to_ui(info.annotation),
                    }
                    for fname, info in model_action.input_schema.model_fields.items()
                ]
            actions_metadata.append({
                "name": model_action.name,
                "label": model_action.label,
                "permission": model_action.permission,
                "icon": model_action.icon,
                "has_input_schema": model_action.input_schema is not None,
                "input_fields": schema_fields,
                })

        metadata["actions"] = actions_metadata
        cls._metadata_cache[cache_key] = metadata
        return metadata


def _pydantic_type_to_ui(annotation: Any) -> str:
    """Map a Pydantic field annotation to a simple UI type string."""
    from typing import get_origin, get_args, Union

    if get_origin(annotation) is Union:
        args = [a for a in get_args(annotation) if a is not type(None)]
        annotation = args[0] if args else str

    if annotation is bool:
        return "boolean"
    if annotation is int:
        return "number"
    if annotation is float:
        return "number"
    try:
        from datetime import datetime, date
        if annotation is datetime:
            return "datetime"
        if annotation is date:
            return "date"
    except ImportError:
        pass
    return "string"
