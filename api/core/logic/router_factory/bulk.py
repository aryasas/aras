import logging
from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session
from typing import List, Type, Any, Optional
from pydantic import BaseModel, ValidationError

from .helpers import (
    _inject_scope_payload, _check_scope_ownership, _trigger_invalidation,
    _broadcast_update
)
from ...lib.database import get_db
from ...logic.permissions import check_permissions
from ...exceptions import ValidationException, ResourceNotFoundException, ArasException
from ...response import ok
from ...base.model import Model as ArasModel

def register_bulk_routes(router: APIRouter, model_class: Type[Any]):

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
            _trigger_invalidation(db, model_class, item)
            _broadcast_update(model_class, "record_deleted", item_id)
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
                event = "record_created"
                if current_id := parent_payload.get("id"):
                    parent_item = model_class.get(db, current_id)
                    if not parent_item:
                        raise ResourceNotFoundException("Item not found")
                    _check_scope_ownership(model_class, request, parent_item)
                    parent_item.update_self(db, parent_payload, user_id=user.id)
                    event = "record_updated"
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
                        _broadcast_update(child_model, "record_created", None)
                    except Exception as ce:
                        child_errors.append(str(ce))
                db.commit()
                _broadcast_update(model_class, event, parent_item.id)
                result = parent_item.to_dict()
                if child_errors:
                    result["child_errors"] = child_errors
                return ok(result, "Saved successfully.")
            except Exception as e:
                db.rollback()
                raise ArasException("Internal Server Error", detail=str(e))

        # Standard list of batch ops
        try:
            operations = [_BatchOp(**op) for op in (body if isinstance(body, list) else [])]
        except (ValidationError, TypeError):
            raise ValidationException("Body must be a list of batch operations or {parent, children}.")
        results = []
        try:
            for op in operations:
                if op.action == "create":
                    payload = _inject_scope_payload(model_class, request, op.data or {})
                    item = model_class.create(db, payload, user_id=user.id)
                    results.append({"action": "create", "id": item.id, "status": "ok"})
                    _trigger_invalidation(db, model_class, item)
                    _broadcast_update(model_class, "record_created", item.id)
                elif op.action == "update":
                    if not op.id:
                        raise ValidationException("Update requires ID.")
                    item = model_class.get(db, op.id)
                    if not item:
                        raise ResourceNotFoundException("Item not found")
                    _check_scope_ownership(model_class, request, item)
                    item.update_self(db, op.data or {}, user_id=user.id)
                    results.append({"action": "update", "id": op.id, "status": "ok"})
                    _trigger_invalidation(db, model_class, item)
                    _broadcast_update(model_class, "record_updated", op.id)
                elif op.action == "delete":
                    if not op.id:
                        raise ValidationException("Delete requires ID.")
                    item = model_class.get(db, op.id)
                    if not item:
                        raise ResourceNotFoundException("Item not found")
                    _check_scope_ownership(model_class, request, item)
                    item.delete_self(db, user_id=user.id)
                    results.append({"action": "delete", "id": op.id, "status": "ok"})
                    _trigger_invalidation(db, model_class, item)
                    _broadcast_update(model_class, "record_deleted", op.id)
                else:
                    raise ValidationException(f"Unknown action: {op.action}")
        except Exception as e:
            db.rollback()
            raise ArasException("Internal Server Error", detail=str(e))
        db.commit()
        return ok({"results": results, "count": len(results)}, "Batch operation completed.")
