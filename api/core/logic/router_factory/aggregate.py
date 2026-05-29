import json
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from typing import Type, Any, Optional

from .helpers import _apply_scope_filters
from ...lib.database import get_db
from ...logic.permissions import check_permissions
from ...exceptions import ValidationException
from ...response import ok

# gemini-flash
def register_aggregate_routes(router: APIRouter, model_class: Type[Any], allow_public: bool):
    @router.get("/aggregate")
    def aggregate_items(
        request: Request,
        field: str = Query(..., description="Field to aggregate"),
        agg_func: str = Query(..., alias="func", description="Aggregation function: sum, count, avg, min, max"),
        group_by: Optional[str] = Query(None, description="Field to group by"),
        filters: Optional[str] = None,
        db: Session = Depends(get_db),
        _: Any = Depends(check_permissions(model_class.__tablename__, "READ", allow_public=allow_public))
    ):
        """Performs aggregation on a specified field, optionally grouped."""
        parsed_filters = None
        if filters:
            try: parsed_filters = json.loads(filters)
            except (json.JSONDecodeError, TypeError): raise ValidationException("Invalid filters format. Must be JSON.")
        parsed_filters = _apply_scope_filters(model_class, request, list(parsed_filters or []))
        target_column = getattr(model_class, field, None)
        if not target_column: raise ValidationException(f"Field '{field}' not found in model.")
        stmt = select(model_class)
        stmt = model_class.apply_filters(stmt, parsed_filters)
        subq = stmt.subquery()
        if group_by:
            group_col_obj = getattr(model_class, group_by, None)
            if not group_col_obj: raise ValidationException(f"Group by field '{group_by}' not found.")
            group_col = subq.c[group_by]
            agg_col = subq.c[field]
            if agg_func == "count": agg_expr = func.count(agg_col)
            elif agg_func == "sum": agg_expr = func.sum(agg_col)
            elif agg_func == "avg": agg_expr = func.avg(agg_col)
            elif agg_func == "min": agg_expr = func.min(agg_col)
            elif agg_func == "max": agg_expr = func.max(agg_col)
            else: raise ValidationException(f"Invalid aggregation function: {agg_func}")
            results = db.execute(select(group_col, agg_expr).group_by(group_col)).all()
            groups = [{"group": row[0], "value": row[1]} for row in results]
            return ok({"groups": groups}, f"Aggregation by {group_by} completed.")
        agg_col = subq.c[field]
        if agg_func == "count": agg_expr = func.count()
        elif agg_func == "sum": agg_expr = func.sum(agg_col)
        elif agg_func == "avg": agg_expr = func.avg(agg_col)
        elif agg_func == "min": agg_expr = func.min(agg_col)
        elif agg_func == "max": agg_expr = func.max(agg_col)
        else: raise ValidationException(f"Invalid aggregation function: {agg_func}")
        aggregate_value = db.scalar(select(agg_expr).select_from(subq))
        return ok({"value": aggregate_value}, f"{agg_func.capitalize()} of {field} retrieved successfully.")
