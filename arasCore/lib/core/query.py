"""
arasCore/lib/query.py — ArasQuery: uniform list/filter/paginate/sort helper.

Usage:
    from arasCore.lib.core.query import ArasQuery
    result = ArasQuery(MyModel, request.args, searchable=["name","email"]).run()
    # result.data, result.meta (page, per_page, total, total_pages)
"""
from __future__ import annotations

import re
from dataclasses import dataclass


DEFAULT_PER_PAGE = 50
MAX_PER_PAGE = 500


@dataclass
class QueryResult:
    data: list
    meta: dict


class ArasQuery:
    """
    Uniform list/filter/paginate/sort helper.

    Supports:
        ?page=1&per_page=50
        ?sort=-created_at,name        (- = desc)
        ?q=foo                         (full-text over searchable cols)
        ?filter[field]=value
        ?filter[field__gte]=10         (operators: eq, ne, gte, lte, like, in)
        ?fields=id,name,email          (sparse fieldsets)
    """

    _OP_MAP = {
        "eq":   lambda col, v: col == v,
        "ne":   lambda col, v: col != v,
        "gte":  lambda col, v: col >= v,
        "lte":  lambda col, v: col <= v,
        "like": lambda col, v: col.ilike(f"%{v}%"),
        "in":   lambda col, v: col.in_(v.split(",")),
    }

    def __init__(self, model, args, searchable: list[str] | None = None, filters: list[str] | None = None):
        self._model = model
        self._args = args
        self._searchable = searchable or []
        self._filters = filters or []

    def _apply_filters_and_sort(self, base_query=None):
        """Apply search, filters, and sort to query. Returns query (not paginated)."""
        from sqlalchemy import or_, asc, desc

        q = base_query if base_query is not None else self._model.query
        args = self._args

        # ── search ────────────────────────────────────────────────────────────
        search_term = args.get("q", "").strip() if hasattr(args, "get") else args.get("q", [""])[0].strip()
        if search_term and self._searchable:
            clauses = []
            for col_name in self._searchable:
                col = getattr(self._model, col_name, None)
                if col is not None:
                    try:
                        clauses.append(col.ilike(f"%{search_term}%"))
                    except Exception:
                        pass
            if clauses:
                q = q.filter(or_(*clauses))

        # ── filter[field__op]=value ───────────────────────────────────────────
        filter_pat = re.compile(r"^filter\[(\w+?)(?:__(\w+))?\]$")
        items = args.items(multi=True) if hasattr(args, "items") else args.items()
        for key, value in items:
            m = filter_pat.match(key)
            if not m:
                continue
            col_name, op = m.group(1), m.group(2) or "eq"
            if self._filters and col_name not in self._filters:
                continue
            col = getattr(self._model, col_name, None)
            if col is None:
                continue
            op_fn = self._OP_MAP.get(op)
            if op_fn:
                try:
                    q = q.filter(op_fn(col, value))
                except Exception:
                    pass

        # ── sort ──────────────────────────────────────────────────────────────
        sort_param = args.get("sort", "") if hasattr(args, "get") else ""
        if sort_param:
            for part in sort_param.split(","):
                part = part.strip()
                if not part:
                    continue
                direction = desc if part.startswith("-") else asc
                col_name = part.lstrip("-")
                col = getattr(self._model, col_name, None)
                if col is not None:
                    try:
                        q = q.order_by(direction(col))
                    except Exception:
                        pass

        return q

    def run(self, base_query=None) -> QueryResult:
        """Apply all query params including pagination; returns QueryResult."""
        args = self._args
        q = self._apply_filters_and_sort(base_query)

        # ── pagination ────────────────────────────────────────────────────────
        _get = lambda k, d: args.get(k, d, type=int) if hasattr(args, "get") and callable(getattr(args, "get")) else int(args.get(k, d))
        page = max(1, _get("page", 1))
        per_page = min(max(1, _get("per_page", DEFAULT_PER_PAGE)), MAX_PER_PAGE)
        pag = q.paginate(page=page, per_page=per_page, error_out=False)

        # ── sparse fieldsets ──────────────────────────────────────────────────
        fields_param = args.get("fields", "") if hasattr(args, "get") else ""
        allowed_fields: set[str] | None = None
        if fields_param:
            allowed_fields = {f.strip() for f in fields_param.split(",") if f.strip()}

        def _to_dict(obj) -> dict:
            if hasattr(obj, "to_dict") and callable(obj.to_dict):
                d = obj.to_dict()
            else:
                from datetime import datetime
                d = {}
                for col in obj.__table__.columns:
                    val = getattr(obj, col.name)
                    d[col.name] = val.isoformat() if isinstance(val, datetime) else val
            if allowed_fields:
                d = {k: v for k, v in d.items() if k in allowed_fields}
            return d

        return QueryResult(
            data=[_to_dict(row) for row in pag.items],
            meta={
                "page":        pag.page,
                "per_page":    pag.per_page,
                "total":       pag.total,
                "total_pages": pag.pages,
                "has_next":    pag.has_next,
                "has_prev":    pag.has_prev,
            },
        )
