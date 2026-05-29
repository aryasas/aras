import logging
from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Type, Any

from .helpers import (
    _check_scope_ownership, _apply_scope_filters
)
from ...lib.database import get_db
from ...logic.permissions import check_permissions
from ...exceptions import ValidationException, ResourceNotFoundException
from ...response import ok
from ...base.model import Model as ArasModel

def register_m2m_routes(router: APIRouter, model_class: Type[Any]):
    @router.put("/{item_id}/{m2m_field}")
    def update_m2m_field(
        request: Request,
        item_id: int,
        m2m_field: str,
        ids: List[int] = Body(...),
        db: Session = Depends(get_db),
        user: Any = Depends(check_permissions(model_class.__tablename__, "UPDATE"))
    ):
        m2m_defs = getattr(model_class, "__m2m__", {})
        if m2m_field not in m2m_defs:
            raise ValidationException(f"Field '{m2m_field}' is not a M2M field on this resource.")
        
        item = model_class.get(db, item_id)
        if not item:
            raise ResourceNotFoundException("Item not found")
        _check_scope_ownership(model_class, request, item)

        target_resource = m2m_defs[m2m_field].get("target_resource")
        if target_resource:
            try:
                target_model = ArasModel.get_model(target_resource)
                stmt = select(target_model.id).where(target_model.id.in_(ids))
                stmt = target_model.apply_filters(stmt, _apply_scope_filters(target_model, request, []))
                found_ids = db.scalars(stmt).all()
                if len(found_ids) != len(set(ids)):
                    missing = set(ids) - set(found_ids)
                    raise ValidationException(f"Some target IDs are invalid or out of scope: {list(missing)}")
            except KeyError:
                logging.warning(f"Target model {target_resource} not found for M2M validation. Skipping.")

        item.save_m2m(db, {m2m_field: ids})
        db.commit()

        from ...api.websocket import broadcast_sync
        broadcast_sync("global", {"event": "m2m_update", "resource": model_class.__tablename__, "id": item_id, "field": m2m_field})
        return ok({"id": item_id, m2m_field: ids}, f"M2M field '{m2m_field}' updated.")
