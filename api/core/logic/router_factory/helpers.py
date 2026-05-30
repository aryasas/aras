import json
import logging
from typing import List, Type, Any, Optional, Union, Dict, Set
from fastapi import Request, HTTPException
from sqlalchemy.orm import Session
from pydantic import create_model, ConfigDict, Field as PydanticField
from pydantic.fields import FieldInfo
from typing import get_args, get_origin, Literal as _Literal

from ...lib.database import get_db
from ...logic.permissions import check_permissions
from ...logic.scope import ScopeContext
from ...exceptions import ValidationException, ResourceNotFoundException
from ...base.model import Model as ArasModel
from ...base.validation import Validation

ACTION_PERMISSION_ALIASES = {
    "read": "READ",
    "view": "READ",
    "create": "CREATE",
    "write": "UPDATE",
    "edit": "UPDATE",
    "update": "UPDATE",
    "delete": "DELETE",
}

def _scope_fields(model_class: Type[Any]) -> list[str]:
    """Return the list of scope field names declared on a model via __scoped_by__."""
    raw = getattr(model_class, "__scoped_by__", None) or []
    result = []
    for item in raw:
        result.append(item[0] if isinstance(item, (list, tuple)) else item)
    return result


def _get_scope(request: Request) -> ScopeContext:
    return getattr(getattr(request, "state", None), "scope", None) or ScopeContext()


def _permission_action(action: str) -> str:
    return ACTION_PERMISSION_ALIASES.get(str(action).lower(), str(action).upper())


def _apply_scope_filters(model_class: Type[Any], request: Request, parsed_filters: list) -> list:
    scope = _get_scope(request)
    if not scope:
        return parsed_filters
    col_names = {c.name for c in model_class.__table__.columns}
    for field in _scope_fields(model_class):
        if field not in col_names:
            continue
        val = scope.get(field)
        if val is None:
            continue
        
        if isinstance(val, list):
            parsed_filters.append({"field": field, "op": "in", "value": val})
        else:
            parsed_filters.append({"field": field, "op": "=", "value": val})
    return parsed_filters


def _inject_scope_payload(model_class: Type[Any], request: Request, payload: dict) -> dict:
    scope = _get_scope(request)
    for field in _scope_fields(model_class):
        val = scope.get(field)
        if val is not None:
            if isinstance(val, list) and not val:
                raise ValidationException(
                    f"No active scope for '{field}'. Please select a context first."
                )
            payload[field] = val[0] if isinstance(val, list) else val
        elif not payload.get(field):
            col_names = {c.name for c in model_class.__table__.columns}
            if field in col_names:
                col = model_class.__table__.c[field]
                if not col.nullable and col.default is None and col.server_default is None:
                    raise ValidationException(
                        f"No active scope for '{field}'. Please select a context first."
                    )
    return payload


def _check_scope_ownership(model_class: Type[Any], request: Request, item: Any):
    scope = _get_scope(request)
    if not scope:
        return
    for field in _scope_fields(model_class):
        val = scope.get(field)
        if val is None:
            continue
        item_val = getattr(item, field, None)
        if isinstance(val, list):
            if item_val not in val:
                raise ResourceNotFoundException("Item not found")
        elif item_val != val:
            raise ResourceNotFoundException("Item not found")

def _update_or_create_child_record(db: Any, parent_item: Any, row_data: dict, child_model: Type[ArasModel], fk_column: str, user_id: int, existing_children_map: dict, incoming_payload_ids: set):
    child_id = row_data.get("id")
    row_data_cleaned = {k: v for k, v in row_data.items() if v is not None or k == fk_column}
    row_data_cleaned[fk_column] = parent_item.id

    if child_id is not None and str(child_id) in existing_children_map:
        existing_child_instance = existing_children_map[str(child_id)]
        existing_child_instance.update_self(db, row_data_cleaned, user_id=user_id)
        incoming_payload_ids.add(str(child_id))
    else:
        child_model.create(db, row_data_cleaned, user_id=user_id)

def _delete_orphaned_child_records(db: Any, existing_children_map: dict, incoming_payload_ids: set):
    for existing_id_str, existing_child_instance in existing_children_map.items():
        if existing_id_str not in incoming_payload_ids:
            db.delete(existing_child_instance)

def _save_children(db: Any, parent_item: Any, payload: dict, user_id: int = None):
    child_defs = ArasModel._child_map.get(parent_item.__tablename__, [])

    for child_def in child_defs:
        child_resource_name = child_def["resource"]
        fk_column = child_def["fk_column"]

        if child_resource_name not in payload or not fk_column:
            continue

        incoming_child_rows_data = payload[child_resource_name]
        if not isinstance(incoming_child_rows_data, list):
            continue

        try:
            child_model = ArasModel.get_model(child_resource_name)
        except KeyError:
            logging.warning(f"Child model {child_resource_name} not found in registry. Skipping child sync.")
            continue

        existing_children_db = db.query(child_model).filter(
            getattr(child_model, fk_column) == parent_item.id
        ).all()
        
        existing_children_map = {str(row.id): row for row in existing_children_db if row.id is not None}
        incoming_payload_ids = set()

        for row_data in incoming_child_rows_data:
            if not isinstance(row_data, dict):
                continue
            _update_or_create_child_record(db, parent_item, row_data, child_model, fk_column, user_id, existing_children_map, incoming_payload_ids)
        
        _delete_orphaned_child_records(db, existing_children_map, incoming_payload_ids)
        db.flush()

def _generate_pydantic_schemas(model_class: Type[Any]):
    from ...aras import Aras
    Schema = Aras.Schema.get_for_model(model_class.__tablename__)
    
    if not Schema:
        fields = {}
        system_skip = {'id', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'}
        scope_field_names = set(_scope_fields(model_class))

        for column in model_class.__table__.columns:
            if column.name in system_skip:
                continue

            python_type = Any
# gemini-flash
            try:
                python_type = column.type.python_type
            except NotImplementedError:
                python_type = str

            info = column.info or {}
            _choices = info.get("choices")
            if _choices:
                python_type = _Literal[tuple(_choices)]  # type: ignore[valid-type]

            is_form_hidden = info.get("form_hidden", False)
            is_scope_field = column.name in scope_field_names
            is_read_only = info.get("read_only", False)
            has_default = (
                column.nullable or
                column.default is not None or
                column.server_default is not None or
                is_form_hidden or
                is_scope_field or
                is_read_only
            )

            pydantic_kwargs = {}
            if info.get("min_length") is not None:
                pydantic_kwargs["min_length"] = info["min_length"]
            if info.get("max_length") is not None:
                pydantic_kwargs["max_length"] = info["max_length"]
            if info.get("min_value") is not None:
                pydantic_kwargs["ge"] = info["min_value"]
            if info.get("max_value") is not None:
                pydantic_kwargs["le"] = info["max_value"]
            if info.get("pattern") is not None:
                pydantic_kwargs["pattern"] = info["pattern"]

            default_val = PydanticField(None if has_default else ..., **pydantic_kwargs) if pydantic_kwargs else (None if has_default else ...)
            fields[column.name] = (Optional[python_type] if has_default else python_type, default_val)

        for child_def in ArasModel._child_map.get(model_class.__tablename__, []):
            resource = child_def.get("resource")
            if resource and resource not in fields:
                fields[resource] = (Any, None)

        Schema = create_model(f"{model_class.__name__}Schema", __base__=Validation, **fields)
        Schema.model_config = ConfigDict(from_attributes=True)

    def _make_optional(annotation: Any) -> Any:
        if get_origin(annotation) is Union:
            return annotation
        return Optional[annotation]

    patch_fields: dict[str, Any] = {
        name: (_make_optional(info.annotation), FieldInfo(default=None))
        for name, info in Schema.model_fields.items()
    }
    PatchSchema = create_model(f"{model_class.__name__}PatchSchema", __base__=Validation, **patch_fields)
    PatchSchema.model_config = ConfigDict(from_attributes=True)

    return Schema, PatchSchema


def _broadcast_update(model_class, event: str, item_id: Any):
    from ...api.websocket import broadcast_sync
    id_val = int(item_id) if item_id and str(item_id).isdigit() else item_id
    payload = {"event": event, "resource": model_class.__tablename__, "id": id_val}
    broadcast_sync("dashboard", payload)
    broadcast_sync("global", payload)


def _trigger_invalidation(db: Session, model_class: Type[Any], item: Any):
    from ...logic.ui_generator import UIGenerator
    from ...registry.resource_model import ResourceModel

    if model_class.__tablename__ == "core_resources":
        UIGenerator.invalidate(item.name)
    elif model_class.__tablename__ == "core_fields":
        resource = db.get(ResourceModel, item.resource_id)
        if resource:
            UIGenerator.invalidate(resource.name)
