import json
import csv
import io
import logging
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Type, Any, Optional
from pydantic import create_model, BaseModel, Field as PydanticField, ConfigDict
from typing import Any, Optional, get_args, get_origin, Union, Literal as _Literal
import re as _re


from ..lib.database import get_db
from ..auth.service import get_current_user
from ..logic.permissions import check_permissions
from ..logic.scope import ScopeContext
from ..base.router import Router
from ..exceptions import ArasException, ValidationException, ResourceNotFoundException, PermissionDeniedException, ConflictException
from ..response import ok, err
from ..base.model import Model as ArasModel
from ..base.validation import Validation
from pydantic.fields import FieldInfo

MAX_PER_PAGE = 200
MAX_CSV_IMPORT_BYTES = 5 * 1024 * 1024
ALLOWED_CSV_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel"}
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
        # supports both ("company_id", "table") tuples and plain "company_id" strings
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
        
        # Append the scope constraint to the filters
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
    """Handles updating an existing child record or creating a new one."""
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
    """Deletes child records that were in DB but are no longer in the incoming payload."""
    for existing_id_str, existing_child_instance in existing_children_map.items():
        if existing_id_str not in incoming_payload_ids:
            db.delete(existing_child_instance)

def _save_children(db: Any, parent_item: Any, payload: dict, user_id: int = None):
    """
    Saves child table rows sent alongside a parent record.
    Implements sync semantics:
    - Existing children with matching IDs are updated.
    - Children present in payload but not in DB (no ID or new ID) are created.
    - Existing children not present in payload are deleted.

    This function is critical for handling child table data provided when a parent
    record is created, updated, or patched. It ensures data consistency for child
    collections by synchronizing the database state with the incoming payload.
    """
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
    """
    Generates Pydantic Schema and PatchSchema for a given model_class.
    """
    from ..aras import Aras
    
    # Check for Custom Schema Override
    Schema = Aras.Schema.get_for_model(model_class.__tablename__)
    
    if not Schema:
        # Auto-generate if no custom schema exists
        fields = {}
        # System fields that are never part of the request body
        system_skip = {'id', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'}
        # Scope fields are server-injected; accept them as optional so the frontend need not send them
        scope_field_names = set(_scope_fields(model_class)) # Use module-level _scope_fields

        for column in model_class.__table__.columns:
            if column.name in system_skip:
                continue

            python_type = Any
            try:
                python_type = column.type.python_type
            except:
                python_type = str

            # Pull declarative validation rules from Field(info={...})
            info = column.info or {}

            # Narrow to Literal[...] when info={"choices": [...]} is set.
            _choices = info.get("choices")
            if _choices:
                python_type = _Literal[tuple(_choices)]  # type: ignore[valid-type]

            # Determine if the field is required
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

        # Add child table fields as optional list[dict] so Pydantic accepts them
        for child_def in ArasModel._child_map.get(model_class.__tablename__, []):
            resource = child_def.get("resource")
            if resource and resource not in fields:
                fields[resource] = (Any, None)

        Schema = create_model(f"{model_class.__name__}Schema", __base__=Validation, **fields)
        Schema.model_config = ConfigDict(from_attributes=True)

    # Partial schema for PATCH — every field is Optional
    def _make_optional(annotation: Any) -> Any:
        if get_origin(annotation) is Union:
            return annotation  # already Optional / Union
        return Optional[annotation]

    patch_fields: dict[str, Any] = {
        name: (_make_optional(info.annotation), FieldInfo(default=None))
        for name, info in Schema.model_fields.items()
    }
    PatchSchema = create_model(f"{model_class.__name__}PatchSchema", __base__=Validation, **patch_fields)
    PatchSchema.model_config = ConfigDict(from_attributes=True)

    return Schema, PatchSchema


class RouterFactory(Router):
    """
    Generic factory for generating standardized CRUD routes for any Aras Model.
    Supports Enterprise features: Pagination, Advanced Filtering, Global Search, and Bulk Actions.
    """

    @classmethod
    def create_router(cls, model_class: Type[Any], prefix: str = None):
        """
        Generates a FastAPI APIRouter for the given Aras.Model.
        """
        from ..base.view import View as _View
        _api_tag = _View._auto_register(model_class).title or model_class.__tablename__
        router = APIRouter(
            prefix=prefix or f"/{model_class.__tablename__}",
            tags=[_api_tag]
        )

        Schema, PatchSchema = _generate_pydantic_schemas(model_class)

        # Determine Public Access
        allow_public = getattr(model_class, "__public_read__", False)

        # ── 2. Standard Endpoints (existing CRUD, etc.) ─────────────────────────
        
        @router.get("/metadata", response_model=dict)
        def get_metadata(
            lang: Optional[str] = Query(None),
            db: Session = Depends(get_db),
            _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Returns metadata for dynamic GUI generation with translation support."""
            # Check for Custom View
            from ..aras import Aras
            view = Aras.View.get_for_model(model_class)
            if view:
                data = view.render_metadata(db=db, lang=lang)
                return ok(data, "Metadata retrieved successfully.")

            # Fallback to standard auto-generation
            from ..logic.ui_generator import UIGenerator
            data = UIGenerator.generate_metadata(model_class, db=db, lang=lang)
            return ok(data, "Metadata retrieved successfully.")

        @router.get("/")
        def list_items_slashed(
            request: Request,
            page: int = Query(1, ge=1),
            per_page: int = Query(20, ge=1, le=MAX_PER_PAGE),
            search: Optional[str] = None,
            filters: Optional[str] = None,
            order_by: Optional[str] = None,
            desc: bool = True,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            return list_items(request, page, per_page, search, filters, order_by, desc, db, user)

        @router.get("")
        def list_items(
            request: Request,
            page: int = Query(1, ge=1),
            per_page: int = Query(20, ge=1, le=MAX_PER_PAGE),
            search: Optional[str] = None,
            filters: Optional[str] = None,
            order_by: Optional[str] = None,
            desc: bool = True,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Lists records with pagination, filtering, and search."""
            parsed_filters = None
            if filters:
                try:
                    parsed_filters = json.loads(filters)
                except:
                    raise ValidationException("Invalid filters format. Must be JSON.")

            parsed_filters = _apply_scope_filters(model_class, request, list(parsed_filters or []))

            paginated_data = model_class.paginate(
                db,
                page=page,
                per_page=per_page,
                search=search,
                filters=parsed_filters,
                order_by=order_by,
                desc=desc
            )
            return ok(paginated_data, "Items listed successfully.")

        @router.get("/aggregate")
        def aggregate_items(
            request: Request, # Added request to allow scope filters
            field: str = Query(..., description="Field to aggregate"),
            agg_func: str = Query(..., alias="func", description="Aggregation function: sum, count, avg"),
            filters: Optional[str] = None,
            db: Session = Depends(get_db),
            _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Performs aggregation on a specified field."""
            parsed_filters = None
            if filters:
                try:
                    parsed_filters = json.loads(filters)
                except:
                    raise ValidationException("Invalid filters format. Must be JSON.")
            
            parsed_filters = _apply_scope_filters(model_class, request, list(parsed_filters or []))

            target_column = getattr(model_class, field, None)
            if not target_column:
                raise ValidationException(f"Field '{field}' not found in model.")

            stmt = select(model_class)
            stmt = model_class.apply_filters(stmt, parsed_filters)

            aggregate_value = None
            if agg_func == "count":
                aggregate_value = db.scalar(select(func.count()).select_from(stmt.subquery()))
            elif agg_func == "sum":
                aggregate_value = db.scalar(select(func.sum(target_column)).select_from(stmt.subquery()))
            elif agg_func == "avg":
                aggregate_value = db.scalar(select(func.avg(target_column)).select_from(stmt.subquery()))
            else:
                raise ValidationException(f"Invalid aggregation function: {agg_func}. Supported: sum, count, avg.")
            
            return ok({"value": aggregate_value}, f"{agg_func.capitalize()} of {field} retrieved successfully.")

        @router.get("/export")
        def export_items(
            request: Request, # Add request for scope filters
            search: Optional[str] = None,
            filters: Optional[str] = None,
            order_by: Optional[str] = None,
            desc: bool = True,
            db: Session = Depends(get_db),
            _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Exports records to a CSV file based on current filters and search."""
            parsed_filters = None
            if filters:
                try: parsed_filters = json.loads(filters)
                except: raise ValidationException("Invalid filters format.")

            parsed_filters = _apply_scope_filters(model_class, request, list(parsed_filters or []))

            # 1. Build Query
            stmt = model_class._q()
            stmt = model_class.apply_filters(stmt, parsed_filters)
            stmt = model_class.apply_search(stmt, search)
            
            sort_col = getattr(model_class, order_by) if order_by and hasattr(model_class, order_by) else model_class.id
            stmt = stmt.order_by(sort_col.desc() if desc else sort_col.asc())

            # 2. Define a generator to stream data
            def generate():
                # Write header
                output = io.StringIO()
                fieldnames = [c.name for c in model_class.__table__.columns if c.name not in model_class._SKIP]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                yield output.getvalue()
                output.seek(0) # Reset buffer

                # Stream data row by row
                for item in db.scalars(stmt).yield_per(100): # Yield in batches of 100 for efficiency
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writerow(item.to_dict())
                    yield output.getvalue()

            return StreamingResponse(
                generate(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={model_class.__tablename__}_export.csv"}
            )

        @router.post("/import")
        def import_items(
            file: UploadFile = File(...),
            mapping: Optional[str] = Query(None), # JSON string mapping CSV -> Model
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            """Imports records from a CSV file via background task with optional mapping."""
            if not file.filename.endswith(".csv"):
                raise ValidationException("Only CSV files are supported")
            if file.content_type and file.content_type not in ALLOWED_CSV_TYPES:
                raise ValidationException("Only CSV files are supported")

            parsed_mapping = None
            if mapping:
                try: parsed_mapping = json.loads(mapping)
                except: raise ValidationException("Invalid mapping format")

            content = file.file.read(MAX_CSV_IMPORT_BYTES + 1)
            if len(content) > MAX_CSV_IMPORT_BYTES:
                raise ValidationException("CSV import file is too large")
            stream = io.StringIO(content.decode("utf-8"))
            reader = csv.DictReader(stream)

            # Read all rows into memory to pass to background task
            data_to_import = list(reader)

            from ..manager.task_manager import TaskManager
            task_id = TaskManager.enqueue_task(
                'task_manager.import_csv_task',
                model_class_name=model_class.__tablename__,
                data=data_to_import,
                user_id=user.id,
                mapping=parsed_mapping
            )
            data = {"message": "CSV import initiated in background", "task_id": task_id}
            return ok(data, data["message"])

        @router.post("/", status_code=status.HTTP_201_CREATED)
        def create_item_slashed(
            request: Request,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            return create_item(request, data, db, user)

        @router.post("", status_code=status.HTTP_201_CREATED)
        def create_item(
            request: Request,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            """Creates a new record with hooks support."""
            payload = _inject_scope_payload(model_class, request, data.model_dump())
            new_item = model_class.create(db, payload, user_id=user.id)
            _save_children(db, new_item, payload, user_id=user.id)
            db.commit()
            return ok(new_item.to_dict(), "Item created successfully.")

        if getattr(model_class, "__soft_delete__", False):
            @router.get("/deleted", tags=[_api_tag])
            def list_deleted(
                request: Request,
                page: int = Query(1, ge=1),
                per_page: int = Query(20, ge=1, le=MAX_PER_PAGE),
                db: Session = Depends(get_db),
                user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=False))
            ):
                """Lists only soft-deleted records."""
                from sqlalchemy import select as sa_select
                stmt = sa_select(model_class).where(model_class.deleted_at.isnot(None))
                stmt = model_class.apply_filters(stmt, _apply_scope_filters(model_class, request, []))
                total = db.scalar(sa_select(func.count()).select_from(stmt.subquery()))
                offset = (page - 1) * per_page
                items = db.scalars(stmt.offset(offset).limit(per_page)).all()
                data = {
                    "items": [i.to_dict() for i in items],
                    "total": total,
                    "page": page,
                    "pages": (total + per_page - 1) // per_page
                }
                return ok(data, "Deleted items listed successfully.")

            @router.post("/{item_id}/restore")
            def restore_item(
                request: Request,
                item_id: int,
                db: Session = Depends(get_db),
                user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
            ):
                """Restores a soft-deleted record."""
                from sqlalchemy import select as sa_select
                item = db.scalar(sa_select(model_class).where(model_class.id == item_id))
                if not item:
                    raise ResourceNotFoundException("Item not found")
                _check_scope_ownership(model_class, request, item)
                if item.deleted_at is None:
                    raise ValidationException("Record is not deleted")
                item.deleted_at = None
                item.updated_by = user.id
                db.commit()
                db.refresh(item)
                return ok(item.to_dict(), "Item restored successfully.")

        @router.get("/{item_id}/linked-documents")
        def get_linked_documents(
            request: Request,
            item_id: int,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=False))
        ):
            """Returns documents linked to this record (reverse FK lookups)."""
            item = model_class.get(db, item_id)
            if not item:
                raise ResourceNotFoundException("Item not found")
            _check_scope_ownership(model_class, request, item)
            docs = item.get_linked_documents(db) if hasattr(item, "get_linked_documents") else []
            return ok(docs, "Linked documents fetched.")

        @router.get("/{item_id}")
        def get_item(
            request: Request,
            item_id: int,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Fetches a single record by ID."""
            item = model_class.get(db, item_id)
            if not item:
                raise ResourceNotFoundException("Item not found")
            _check_scope_ownership(model_class, request, item)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])

            # Child Hydration
            child_defs = ArasModel._child_map.get(model_class.__tablename__, [])
            for child_def in child_defs:
                child_resource_name = child_def["resource"]
                fk_column = child_def["fk_column"]

                if fk_column and child_resource_name:
                    try:
                        child_model_class = ArasModel.get_model(child_resource_name)
                        child_records = db.scalars(
                            select(child_model_class).where(getattr(child_model_class, fk_column) == item_id)
                        ).all()
                        res[child_resource_name] = [rec.to_dict() for rec in child_records]
                        child_model_class.resolve_labels(db, res[child_resource_name])
                    except KeyError:
                        logging.warning(f"Child model {child_resource_name} not found in registry.")
                    except Exception as e:
                        logging.error(f"Error fetching child records for {child_resource_name}: {e}", exc_info=True)

            return ok(res, "Item retrieved successfully.")

        @router.put("/{item_id}")
        def update_item(
            request: Request,
            item_id: int,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Updates an existing record with hooks support."""
            item = model_class.get(db, item_id)
            if not item:
                raise ResourceNotFoundException("Item not found")
            _check_scope_ownership(model_class, request, item)

            payload = data.model_dump(exclude_unset=True)
            item.update_self(db, payload, user_id=user.id)
            _save_children(db, item, payload, user_id=user.id)
            db.commit()
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return ok(res, "Item updated successfully.")

        @router.patch("/{item_id}")
        def patch_item(
            request: Request,
            item_id: int,
            data: PatchSchema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Partially updates an existing record."""
            item = model_class.get(db, item_id)
            if not item:
                raise ResourceNotFoundException("Item not found")
            _check_scope_ownership(model_class, request, item)

            payload = data.model_dump(exclude_unset=True)
            item.update_self(db, payload, user_id=user.id)
            _save_children(db, item, payload, user_id=user.id)
            db.commit()
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return ok(res, "Item patched successfully.")

        @router.delete("/{item_id}")
        def delete_item(
            request: Request,
            item_id: int,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "DELETE"))
        ):
            """Deletes or soft-deletes a record."""
            item = model_class.get(db, item_id)
            if not item:
                raise ResourceNotFoundException("Item not found")
            _check_scope_ownership(model_class, request, item)

            item.delete_self(db, user_id=user.id)
            db.commit()
            return ok({"id": item_id}, "Item deleted successfully.")

        @router.post("/bulk-delete")
        def bulk_delete(
            request: Request,
            ids: List[int],
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "DELETE"))
        ):
            """Performs bulk deletion of multiple records."""
            deleted_count = 0
            for item_id in ids:
                item = model_class.get(db, item_id)
                if not item:
                    raise ResourceNotFoundException("Item not found")
                _check_scope_ownership(model_class, request, item)
                item.delete_self(db, user.id)
                deleted_count += 1
            message = f"Successfully deleted {deleted_count} of {len(ids)} items."
            db.commit()
            return ok({"deleted_count": deleted_count, "requested_count": len(ids)}, message)

        @router.post("/batch-delete")
        def batch_delete(
            request: Request,
            body: Any = Body(...),
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "DELETE"))
        ):
            """Compatibility endpoint for older clients that send {ids: [...]}."""
            ids = body.get("ids") if isinstance(body, dict) else body
            if not isinstance(ids, list) or not all(isinstance(item_id, int) for item_id in ids):
                raise ValidationException("Body must be a list of IDs or an object with an ids list.")
            return bulk_delete(request, ids, db, user)

        class _BatchOp(BaseModel):
            action: str  # "create" | "update" | "delete"
            id: Optional[int] = None
            data: Optional[dict] = None

        @router.post("/batch")
        def batch_operations(
            request: Request,
            body: Any = Body(...),
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Executes mixed create/update/delete operations, or saves parent+children atomically."""
            # {parent, children} shape — save parent then its children
            if isinstance(body, dict) and "parent" in body:
                try:
                    parent_payload = _inject_scope_payload(model_class, request, body["parent"])
                    children = body.get("children") or []
                    if current_id := parent_payload.get("id"):
                        parent_item = model_class.get(db, current_id)
                        if not parent_item:
                            raise ResourceNotFoundException("Item not found")
                        _check_scope_ownership(model_class, request, parent_item)
                        parent_item.update_self(db, parent_payload, user_id=user.id)
                    else:
                        parent_item = model_class.create(db, parent_payload, user_id=user.id)
                    db.flush()
                    # Save each child group
                    child_errors = []
                    for child_entry in children:
                        child_resource = child_entry.get("resource", "").replace("/", "_").lstrip("_")
                        child_data = child_entry.get("data", {})
                        child_def = next(
                            (c for c in ArasModel._child_map.get(model_class.__tablename__, [])
                             if c["resource"] == child_resource or c["resource"].endswith(child_resource.split("_")[-1])),
                            None
                        )
                        if not child_def:
                            child_errors.append(f"Unknown child resource: {child_resource}")
                            continue
                        fk_column = child_def["fk_column"]
                        child_model = ArasModel.get_model(child_def["resource"])
                        child_data[fk_column] = parent_item.id
                        child_data = _inject_scope_payload(child_model, request, child_data)
                        try:
                            child_model.create(db, child_data, user_id=user.id)
                        except Exception as ce:
                            child_errors.append(str(ce))
                    db.commit()
                    result = parent_item.to_dict()
                    if child_errors:
                        result["child_errors"] = child_errors
                    return ok(result, "Saved successfully.")
                except HTTPException:
                    raise
                except Exception as e:
                    db.rollback()
                    raise ArasException("Internal Server Error", detail=str(e))

            # Standard list of batch ops
            try:
                operations = [_BatchOp(**op) for op in (body if isinstance(body, list) else [])]
            except Exception:
                raise ValidationException("Body must be a list of batch operations or {parent, children}.")
            results = []
            try:
                for op in operations:
                    if op.action == "create":
                        payload = _inject_scope_payload(model_class, request, op.data or {})
                        item = model_class.create(db, payload, user_id=user.id)
                        results.append({"action": "create", "id": item.id, "status": "ok"})
                    elif op.action == "update":
                        if not op.id:
                            raise ValidationException("Update requires ID.")
                        item = model_class.get(db, op.id)
                        if not item:
                            raise ResourceNotFoundException("Item not found")
                        _check_scope_ownership(model_class, request, item)
                        item.update_self(db, op.data or {}, user_id=user.id)
                        results.append({"action": "update", "id": op.id, "status": "ok"})
                    elif op.action == "delete":
                        if not op.id:
                            raise ValidationException("Delete requires ID.")
                        item = model_class.get(db, op.id)
                        if not item:
                            raise ResourceNotFoundException("Item not found")
                        _check_scope_ownership(model_class, request, item)
                        item.delete_self(db, user_id=user.id)
                        results.append({"action": "delete", "id": op.id, "status": "ok"})
                    else:
                        raise ValidationException(f"Unknown action: {op.action}")
            except HTTPException:
                raise
            except Exception as e:
                db.rollback()
                raise ArasException("Internal Server Error", detail=str(e))
            db.commit()
            
            data = {"results": results, "count": len(results)}
            return ok(data, "Batch operation completed.")
        
        # ── 3. Custom Model Actions ───────────────────────────────────────────
        for action_name, model_action in model_class._actions.items():
            # Create a dynamic Pydantic model for the action's input if schema is provided
            ActionInputSchema = model_action.input_schema
            
            # Helper to create the route with correct closure
            def create_action_route(name, action):
                InputModel = ActionInputSchema
                
                if InputModel:
                    @router.post(f"/{{item_id}}/action/{name}", response_model=dict)
                    def run_custom_action(
                        request: Request,
                        item_id: int,
                        input_data: InputModel,
                        db: Session = Depends(get_db),
                        user: Any = Depends(check_permissions(model_class.__tablename__, _permission_action(action.permission)))
                    ):
                        item = model_class.get(db, item_id)
                        if not item:
                            raise ResourceNotFoundException("Item not found")
                        _check_scope_ownership(model_class, request, item)
                        
                        try:
                            # Pass input data to handler
                            handler = getattr(item, action.handler.__name__)
                            result = handler(db, input_data)
                            db.commit()
                            message = f"Action '{name}' completed successfully."
                            return ok({"result": result}, message)
                        except ArasException:
                            db.rollback()
                            raise
                        except Exception as e:
                            db.rollback()
                            logging.error(f"Error running custom action '{name}' for {model_class.__tablename__}.{item_id}: {e}", exc_info=True)
                            raise ArasException("Internal Server Error", detail=str(e))
                else:
                    @router.post(f"/{{item_id}}/action/{name}", response_model=dict)
                    def run_custom_action(
                        request: Request,
                        item_id: int,
                        db: Session = Depends(get_db),
                        user: Any = Depends(check_permissions(model_class.__tablename__, _permission_action(action.permission)))
                    ):
                        item = model_class.get(db, item_id)
                        if not item:
                            raise ResourceNotFoundException("Item not found")
                        _check_scope_ownership(model_class, request, item)
                        
                        try:
                            handler = getattr(item, action.handler.__name__)
                            result = handler(db)
                            db.commit()
                            message = f"Action '{name}' completed successfully."
                            return ok({"result": result}, message)
                        except ArasException:
                            db.rollback()
                            raise
                        except Exception as e:
                            db.rollback()
                            logging.error(f"Error running custom action '{name}' for {model_class.__tablename__}.{item_id}: {e}", exc_info=True)
                            raise ArasException("Internal Server Error", detail=str(e))
            
            create_action_route(action_name, model_action)

        return router
