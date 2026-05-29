import logging
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Type, Any, Optional

from .helpers import _apply_scope_filters, _check_scope_ownership
from ...lib.database import get_db
from ...logic.permissions import check_permissions
from ...response import ok

def register_search_routes(router: APIRouter, model_class: Type[Any], allow_public: bool):
    @router.get("/search")
    def search_resource(
        request: Request,
        q: str = Query(..., min_length=1),
        limit: int = Query(10, ge=1, le=50),
        db: Session = Depends(get_db),
        _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
    ):
        """Search within this specific resource."""
        stmt = model_class._q().limit(limit)
        stmt = model_class.apply_search(stmt, q)
        stmt = model_class.apply_filters(stmt, _apply_scope_filters(model_class, request, []))
        items = db.scalars(stmt).all()
        return ok([item.to_dict() for item in items], f"Search results for '{q}'")

    @router.get("/lookup")
    def lookup_resource(
        request: Request,
        q: Optional[str] = Query(None),
        limit: int = Query(20, ge=1, le=100),
        db: Session = Depends(get_db),
        _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
    ):
        """Standardized lookup for dropdowns/comboboxes. Returns {id, label}."""
        stmt = model_class._q().limit(limit)
        if q:
            stmt = model_class.apply_search(stmt, q)
        stmt = model_class.apply_filters(stmt, _apply_scope_filters(model_class, request, []))
        items = db.scalars(stmt).all()
        
        results = []
        for item in items:
            # Try common label fields
            label = getattr(item, "name", getattr(item, "title", getattr(item, "label", str(item.id))))
            results.append({"id": item.id, "label": label})
            
        return ok(results, "Lookup results")
