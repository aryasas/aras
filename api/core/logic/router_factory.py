import json
import csv
import io
from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import List, Type, Any, Optional
from pydantic import create_model, BaseModel

from ..lib.database import get_db
from ..auth.service import get_current_user
from ..logic.permissions import check_permissions
from ..logic.scope import ScopeContext
from ..base.router import Router


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


def _apply_scope_filters(model_class: Type[Any], request: Request, parsed_filters: list) -> list:
    scope = _get_scope(request)
    if not scope:
        return parsed_filters
    col_names = {c.name for c in model_class.__table__.columns}
    for field in _scope_fields(model_class):
        val = scope.get(field)
        if val is not None and field in col_names:
            parsed_filters.append({"field": field, "op": "=", "value": val})
    return parsed_filters


def _inject_scope_payload(model_class: Type[Any], request: Request, payload: dict) -> dict:
    scope = _get_scope(request)
    for field in _scope_fields(model_class):
        val = scope.get(field)
        if val is not None:
            payload[field] = val
        elif not payload.get(field):
            col_names = {c.name for c in model_class.__table__.columns}
            if field in col_names:
                col = model_class.__table__.c[field]
                if not col.nullable and col.default is None and col.server_default is None:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No active scope for '{field}'. Please select a context first."
                    )
    return payload


def _check_scope_ownership(model_class: Type[Any], request: Request, item: Any):
    scope = _get_scope(request)
    if not scope:
        return
    for field in _scope_fields(model_class):
        val = scope.get(field)
        if val is not None and getattr(item, field, None) != val:
            raise HTTPException(status_code=404, detail="Item not found")


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

        # ── 1. Dynamic Pydantic Schema Generation ─────────────────────────────
        from ..aras import Aras
        
        # Check for Custom Schema Override
        Schema = Aras.Schema.get_for_model(model_class.__tablename__)
        
        if not Schema:
            # Auto-generate if no custom schema exists
            fields = {}
            # System fields that are never part of the request body
            system_skip = {'id', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by'}

            from pydantic import Field as PydanticField
            import re as _re

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
                    from typing import Literal as _Literal
                    python_type = _Literal[tuple(_choices)]  # type: ignore[valid-type]

                # Determine if the field is required
                is_form_hidden = info.get("form_hidden", False)
                has_default = (
                    column.nullable or
                    column.default is not None or
                    column.server_default is not None or
                    is_form_hidden
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

            from ..base.validation import Validation
            from pydantic import ConfigDict
            Schema = create_model(f"{model_class.__name__}Schema", __base__=Validation, **fields)
            Schema.model_config = ConfigDict(from_attributes=True)

        # Partial schema for PATCH — every field is Optional
        from typing import get_args, get_origin, Union
        from pydantic.fields import FieldInfo
        def _make_optional(annotation: Any) -> Any:
            if get_origin(annotation) is Union:
                return annotation  # already Optional / Union
            return Optional[annotation]

        patch_fields: dict[str, Any] = {
            name: (_make_optional(info.annotation), FieldInfo(default=None))
            for name, info in Schema.model_fields.items()
        }
        from pydantic import ConfigDict as _ConfigDict
        from ..base.validation import Validation as _Validation
        PatchSchema = create_model(f"{model_class.__name__}PatchSchema", __base__=_Validation, **patch_fields)
        PatchSchema.model_config = _ConfigDict(from_attributes=True)

        # Determine Public Access
        allow_public = getattr(model_class, "__public_read__", False)

        # ── 2. Standard Endpoints (existing CRUD, etc.) ─────────────────────────
        
        @router.get("/metadata", response_model=dict)
        async def get_metadata(
            lang: Optional[str] = Query(None),
            db: Session = Depends(get_db),
            _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Returns metadata for dynamic GUI generation with translation support."""
            # Check for Custom View
            from ..aras import Aras
            view = Aras.View.get_for_model(model_class)
            if view:
                return view.render_metadata(db=db, lang=lang)
            
            # Fallback to standard auto-generation
            from ..logic.ui_generator import UIGenerator
            return UIGenerator.generate_metadata(model_class, db=db, lang=lang)

        @router.get("/")
        async def list_items_slashed(
            request: Request,
            page: int = Query(1, ge=1),
            per_page: int = Query(20, ge=1, le=999999),
            search: Optional[str] = None,
            filters: Optional[str] = None,
            order_by: Optional[str] = None,
            desc: bool = True,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            return await list_items(request, page, per_page, search, filters, order_by, desc, db, user)

        @router.get("")
        async def list_items(
            request: Request,
            page: int = Query(1, ge=1),
            per_page: int = Query(20, ge=1, le=999999),
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
                    raise HTTPException(status_code=400, detail="Invalid filters format. Must be JSON.")

            parsed_filters = _apply_scope_filters(model_class, request, list(parsed_filters or []))

            return model_class.paginate(
                db,
                page=page,
                per_page=per_page,
                search=search,
                filters=parsed_filters,
                order_by=order_by,
                desc=desc
            )

        @router.get("/export")
        async def export_items(
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
                except: raise HTTPException(status_code=400, detail="Invalid filters format")

            # 1. Build Query
            stmt = model_class._q()
            stmt = model_class.apply_filters(stmt, parsed_filters)
            stmt = model_class.apply_search(stmt, search)
            
            sort_col = getattr(model_class, order_by) if order_by and hasattr(model_class, order_by) else model_class.id
            stmt = stmt.order_by(sort_col.desc() if desc else sort_col.asc())

            # 2. Fetch All (Warning: Large datasets might need chunking, but for MVP we fetch all)
            items = db.scalars(stmt).all()
            if not items:
                raise HTTPException(status_code=404, detail="No items to export")

            # 3. Create CSV in Memory
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[c.name for c in model_class.__table__.columns])
            writer.writeheader()
            for item in items:
                writer.writerow(item.to_dict())
            
            output.seek(0)
            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={model_class.__tablename__}_export.csv"}
            )

        @router.post("/import")
        async def import_items(
            file: UploadFile = File(...),
            mapping: Optional[str] = Query(None), # JSON string mapping CSV -> Model
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            """Imports records from a CSV file via background task with optional mapping."""
            if not file.filename.endswith(".csv"):
                raise HTTPException(status_code=400, detail="Only CSV files are supported")

            parsed_mapping = None
            if mapping:
                try: parsed_mapping = json.loads(mapping)
                except: raise HTTPException(status_code=400, detail="Invalid mapping format")

            content = await file.read()
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

            return {"message": "CSV import initiated in background", "task_id": task_id}
        @router.post("/", status_code=status.HTTP_201_CREATED)
        async def create_item_slashed(
            request: Request,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            return await create_item(request, data, db, user)

        @router.post("", status_code=status.HTTP_201_CREATED)
        async def create_item(
            request: Request,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "CREATE"))
        ):
            """Creates a new record with hooks support."""
            payload = _inject_scope_payload(model_class, request, data.model_dump())
            new_item = model_class.create(db, payload, user_id=user.id)
            return new_item.to_dict()

        @router.get("/{item_id}")
        async def get_item(
            request: Request,
            item_id: int,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
        ):
            """Fetches a single record by ID."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            _check_scope_ownership(model_class, request, item)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

        @router.put("/{item_id}")
        async def update_item(
            request: Request,
            item_id: int,
            data: Schema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Updates an existing record with hooks support."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            _check_scope_ownership(model_class, request, item)

            payload = data.model_dump(exclude_unset=True)
            item.update_self(db, payload, user_id=user.id)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

        @router.patch("/{item_id}")
        async def patch_item(
            request: Request,
            item_id: int,
            data: PatchSchema,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Partially updates an existing record."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            _check_scope_ownership(model_class, request, item)

            payload = data.model_dump(exclude_unset=True)
            item.update_self(db, payload, user_id=user.id)
            res = item.to_dict()
            model_class.resolve_labels(db, [res])
            return res

        @router.delete("/{item_id}")
        async def delete_item(
            item_id: int,
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "DELETE"))
        ):
            """Deletes or soft-deletes a record."""
            item = model_class.get(db, item_id)
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")

            item.delete_self(db, user_id=user.id)
            return {"message": "Deleted successfully", "id": item_id}

        if getattr(model_class, "__soft_delete__", False):
            @router.get("/deleted", tags=[_api_tag])
            async def list_deleted(
                page: int = Query(1, ge=1),
                per_page: int = Query(20, ge=1, le=999999),
                db: Session = Depends(get_db),
                user: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=False))
            ):
                """Lists only soft-deleted records."""
                from sqlalchemy import select as sa_select
                stmt = sa_select(model_class).where(model_class.deleted_at.isnot(None))
                total = db.scalar(sa_select(func.count()).select_from(stmt.subquery()))
                offset = (page - 1) * per_page
                items = db.scalars(stmt.offset(offset).limit(per_page)).all()
                return {
                    "items": [i.to_dict() for i in items],
                    "total": total,
                    "page": page,
                    "pages": (total + per_page - 1) // per_page
                }

            @router.post("/{item_id}/restore")
            async def restore_item(
                item_id: int,
                db: Session = Depends(get_db),
                user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
            ):
                """Restores a soft-deleted record."""
                from sqlalchemy import select as sa_select
                item = db.scalar(sa_select(model_class).where(model_class.id == item_id))
                if not item:
                    raise HTTPException(status_code=404, detail="Item not found")
                if item.deleted_at is None:
                    raise HTTPException(status_code=400, detail="Record is not deleted")
                item.deleted_at = None
                item.updated_by = user.id
                db.commit()
                db.refresh(item)
                return item.to_dict()

        @router.post("/bulk-delete")
        async def bulk_delete(
            ids: List[int],
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "DELETE"))
        ):
            """Performs bulk deletion of multiple records."""
            deleted_count = 0
            for item_id in ids:
                item = model_class.get(db, item_id)
                if item:
                    try:
                        item.delete_self(db, user_id=user.id)
                        deleted_count += 1
                    except Exception as e:
                        print(f"[Bulk Delete] Failed to delete item {item_id}: {e}")
            return {"message": f"Successfully deleted {deleted_count} items", "deleted_count": deleted_count}

        class _BatchOp(BaseModel):
            action: str  # "create" | "update" | "delete"
            id: Optional[int] = None
            data: Optional[dict] = None

        @router.post("/batch")
        async def batch_operations(
            operations: List[_BatchOp],
            db: Session = Depends(get_db),
            user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
        ):
            """Executes mixed create/update/delete operations atomically."""
            results = []
            try:
                for op in operations:
                    if op.action == "create":
                        item = model_class.create(db, op.data or {}, user_id=user.id)
                        results.append({"action": "create", "id": item.id, "status": "ok"})
                    elif op.action == "update":
                        if not op.id:
                            raise HTTPException(status_code=400, detail="update requires id")
                        item = model_class.get(db, op.id)
                        if not item:
                            results.append({"action": "update", "id": op.id, "status": "not_found"})
                            continue
                        item.update_self(db, op.data or {}, user_id=user.id)
                        results.append({"action": "update", "id": op.id, "status": "ok"})
                    elif op.action == "delete":
                        if not op.id:
                            raise HTTPException(status_code=400, detail="delete requires id")
                        item = model_class.get(db, op.id)
                        if not item:
                            results.append({"action": "delete", "id": op.id, "status": "not_found"})
                            continue
                        item.delete_self(db, user_id=user.id)
                        results.append({"action": "delete", "id": op.id, "status": "ok"})
                    else:
                        raise HTTPException(status_code=400, detail=f"Unknown action: {op.action}")
            except HTTPException:
                raise
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=str(e))
            return {"results": results, "count": len(results)}
        
        # ── 3. Custom Model Actions ───────────────────────────────────────────
        for action_name, model_action in model_class._actions.items():
            # Create a dynamic Pydantic model for the action's input if schema is provided
            ActionInputSchema = model_action.input_schema
            
            # Helper to create the route with correct closure
            def create_action_route(name, action):
                InputModel = ActionInputSchema
                
                if InputModel:
                    @router.post(f"/{{item_id}}/action/{name}", response_model=dict)
                    async def run_custom_action(
                        item_id: int,
                        input_data: InputModel,
                        db: Session = Depends(get_db),
                        user: Any = Depends(check_permissions(model_class.__tablename__, action.permission))
                    ):
                        item = model_class.get(db, item_id)
                        if not item:
                            raise HTTPException(status_code=404, detail="Item not found")
                        
                        try:
                            # Pass input data to handler
                            handler = getattr(item, action.handler.__name__)
                            result = handler(input_data)
                            db.commit()
                            return {"message": f"Action '{name}' completed", "result": result}
                        except Exception as e:
                            db.rollback()
                            raise HTTPException(status_code=500, detail=str(e))
                else:
                    @router.post(f"/{{item_id}}/action/{name}", response_model=dict)
                    async def run_custom_action(
                        item_id: int,
                        db: Session = Depends(get_db),
                        user: Any = Depends(check_permissions(model_class.__tablename__, action.permission))
                    ):
                        item = model_class.get(db, item_id)
                        if not item:
                            raise HTTPException(status_code=404, detail="Item not found")
                        
                        try:
                            handler = getattr(item, action.handler.__name__)
                            result = handler()
                            db.commit()
                            return {"message": f"Action '{name}' completed", "result": result}
                        except Exception as e:
                            db.rollback()
                            raise HTTPException(status_code=500, detail=str(e))
            
            create_action_route(action_name, model_action)

        return router
