import logging
from fastapi import APIRouter, Depends, Body, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from ..lib.database import get_db
from ..lib.query_builder import QueryBuilder
from ..auth.service import get_current_user
from ..base.validation import Validation
from ..logic.permissions import RBAC

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Generic Query API"])


class QueryRequest(Validation):
    filters: List[Dict[str, Any]] = []


@router.post("/{resource_name}/query")
def execute_query(
    fastapi_request: Request,
    resource_name: str,
    request: QueryRequest = Body(...),
    db: Session = Depends(get_db),
    current_user: Optional[Any] = Depends(get_current_user)
):
    """Execute a structured query against any registered resource."""
    from ..base.model import Model

    model_class = Model._registry.get(resource_name)
    if not model_class:
        for cls in Model._registry.values():
            if getattr(cls, "__tablename__", None) == resource_name:
                model_class = cls
                break

    if not model_class:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_name}' not found")

    if not current_user.is_admin and not RBAC.has_permission(db, current_user, model_class.__tablename__, "READ"):
        raise HTTPException(status_code=403, detail=f"No READ permission on {model_class.__tablename__}")

    filters = list(request.filters or [])
    scope = getattr(getattr(fastapi_request, "state", None), "scope", None)
    if scope:
        scoped_by = getattr(model_class, "__scoped_by__", None) or []
        col_names = {c.name for c in model_class.__table__.columns}
        for item in scoped_by:
            field = item[0] if isinstance(item, (list, tuple)) else item
            if field not in col_names:
                continue
            value = scope.get(field)
            if value is None:
                continue
            filters.append({"field": field, "op": "in" if isinstance(value, list) else "==", "value": value})

    try:
        results = QueryBuilder.execute(db, model_class, filters)
        return {"items": [item.to_dict() for item in results]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search")
def global_search(
    request: Request,
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_user)
):
    """Searches across all registered searchable resources the user has READ access to."""
    from ..base.model import Model

    allowed_resources: Optional[set] = None
    if not current_user.is_admin:
        allowed_resources = RBAC.get_readable_resources(db, current_user)

    results = []
    search_count = 0

    for name, model_class in Model._registry.items():
        if name != getattr(model_class, "__tablename__", None):
            continue

        if getattr(model_class, "__searchable__", True) is False:
            continue

        if allowed_resources is not None and model_class.__tablename__ not in allowed_resources:
            continue

        search_fields = _get_search_fields(model_class)
        if not search_fields:
            continue

        try:
            stmt = model_class._q().limit(10)
            stmt = model_class.apply_search(stmt, q, fields=search_fields)
            scope = getattr(getattr(request, "state", None), "scope", None)
            if scope:
                scoped_by = getattr(model_class, "__scoped_by__", None) or []
                col_names = {c.name for c in model_class.__table__.columns}
                for item in scoped_by:
                    field = item[0] if isinstance(item, (list, tuple)) else item
                    if field not in col_names:
                        continue
                    value = scope.get(field)
                    if value is None:
                        continue
                    column = getattr(model_class, field)
                    stmt = stmt.where(column.in_(value) if isinstance(value, list) else column == value)
            items = db.scalars(stmt).all()

            for item in items:
                label = getattr(item, "name",
                        getattr(item, "title",
                        getattr(item, "username",
                        getattr(item, "number", f"{model_class.__name__} #{item.id}"))))
                results.append({
                    "resource": model_class.__tablename__,
                    "id": item.id,
                    "label": str(label),
                    "type": getattr(model_class, "__title__", model_class.__name__)
                })
                search_count += 1
        except Exception as e:
            logger.error(f"Global search error in {name}: {e}")
            continue

        if search_count >= 50:
            break

    return results


def _get_search_fields(model_class: Any) -> List[str]:
    """Returns search fields for a model, cached on the class after first call."""
    cached = getattr(model_class, "_search_fields_cache", None)
    if cached is not None:
        return cached

    if hasattr(model_class, "__searchable_fields__"):
        fields = list(model_class.__searchable_fields__)
    else:
        fields = []
        for c in model_class.__table__.columns:
            type_name = str(c.type).upper()
            if c.info.get("searchable", False) or \
               "VARCHAR" in type_name or "TEXT" in type_name or "STRING" in type_name:
                fields.append(c.name)

    model_class._search_fields_cache = fields
    return fields
