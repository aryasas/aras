import logging
from typing import List, Any, Optional, Type, Dict
from sqlalchemy import select, func, or_, String, Table
from sqlalchemy.orm import Session
from ...lib.helpers import to_label_case

class QueryMixin:
    """Database query and filtering helpers for Model."""

    @classmethod
    def get_ui_fields(cls):
        """Returns list of non-system, non-hidden columns for UI generation."""
        system_fields = getattr(cls, "_SYSTEM", {"id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at"})
        return [
            c for c in cls.__table__.columns 
            if c.name not in system_fields and not c.info.get("hidden", False)
        ]

    @classmethod
    def _q(cls, active_only=False):
        """Standardized query builder with soft-delete support."""
        stmt = select(cls)
        if getattr(cls, "__soft_delete__", False):
            stmt = stmt.where(cls.deleted_at.is_(None))
        if active_only and hasattr(cls, "is_active"):
            stmt = stmt.where(cls.is_active == True)
        return stmt

    @classmethod
    def apply_filters(cls, stmt, filters: List[dict] = None):
        """Apply advanced filters with operators."""
        if not filters:
            return stmt

        operators = {
            "=": lambda col, val: col == val,
            "!=": lambda col, val: col != val,
            ">": lambda col, val: col > val,
            ">=": lambda col, val: col >= val,
            "<": lambda col, val: col < val,
            "<=": lambda col, val: col <= val,
            "ilike": lambda col, val: col.ilike(f"%{val}%"),
            "between": lambda col, val: col.between(val[0], val[1]) if isinstance(val, list) and len(val) == 2 else None,
            "in": lambda col, val: col.in_(val) if isinstance(val, list) else None,
        }
            
        for f in filters:
            field = f.get("field")
            op = f.get("op", "=")
            val = f.get("value")
            
            if not field or not hasattr(cls, field): continue
            col = getattr(cls, field)
            
            try:
                if op == "shared_scope" and isinstance(val, dict):
                    direct_id = val["direct"]
                    other_ids = val["others"]
                    col_obj = getattr(cls, field)
                    is_shared_col = getattr(cls, "is_shared", None)
                    if is_shared_col is not None and other_ids:
                        stmt = stmt.where(
                            or_(
                                col_obj == direct_id,
                                (col_obj.in_(other_ids)) & (is_shared_col == True)
                            )
                        )
                    else:
                        stmt = stmt.where(col_obj == direct_id)
                elif op in operators:
                    filter_func = operators[op]
                    clause = filter_func(col, val)
                    if clause is not None:
                        stmt = stmt.where(clause)
            except Exception as e:
                logging.warning(f"Error applying filter '{field} {op} {val}' to {cls.__name__}: {e}")
                continue
        return stmt

    @classmethod
    def apply_search(cls, stmt, term: str = None, fields: list = None):
        """Apply global search across specified fields."""
        if not term:
            return stmt
            
        search_fields = fields or list(getattr(cls, "__display_fields__", []))
        if not search_fields:
            search_fields = [
                c.name for c in cls.__table__.columns 
                if c.info.get("searchable", False) or isinstance(c.type, String)
            ]
            
        conditions = []
        for f in search_fields:
            if hasattr(cls, f):
                conditions.append(getattr(cls, f).ilike(f"%{term}%"))
                
        if conditions:
            stmt = stmt.where(or_(*conditions))
        return stmt

    @classmethod
    def paginate(cls, db: Session, page: int = 1, per_page: int = 20, 
                 active_only=False, filters: List[dict] = None, search: str = None, 
                 order_by: str = None, desc: bool = True, **kwargs):
        """Enhanced pagination with filtering and searching."""
        stmt = cls._q(active_only)
        if kwargs:
            stmt = stmt.filter_by(**kwargs)
        stmt = cls.apply_filters(stmt, filters)
        stmt = cls.apply_search(stmt, search)
        
        sort_col = getattr(cls, order_by) if order_by and hasattr(cls, order_by) else cls.id
        stmt = stmt.order_by(sort_col.desc() if desc else sort_col.asc())

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = db.scalars(stmt.offset((page - 1) * per_page).limit(per_page)).all()

        results = [item.to_dict() for item in items]
        cls.resolve_labels(db, results)
        cls.resolve_m2m(db, results)

        return {
            "items": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 1
        }

    @classmethod
    def resolve_labels(cls, db: Session, items: List[dict]):
        """Automatically fetches human-readable labels for foreign key and choice columns."""
        if not items: return

        # Resolve choices fields
        for col in cls.__table__.columns:
            choices = col.info.get("choices")
            if not choices: continue
            label_map = {c: to_label_case(c) for c in choices}
            for item in items:
                val = item.get(col.name)
                if val in label_map:
                    item[f"{col.name}_label"] = label_map[val]

        for col in cls.__table__.columns:
            display_col = col.info.get("display_column")
            if not display_col: continue

            target_table = None
            if col.foreign_keys:
                for fk in col.foreign_keys:
                    target_table = fk.column.table.name
                    break
            if not target_table: continue
            
            ids = {item[col.name] for item in items if item.get(col.name) is not None}
            if not ids: continue
            
            table = cls.metadata.tables.get(target_table)
            if table is None: continue
            
            link_col_name = col.info.get("link_column", "id")
            link_col = table.columns.get(link_col_name)
            display_col_obj = table.columns.get(display_col)
            
            if link_col is None or display_col_obj is None: continue
            
            try:
                mapping = {row[0]: row[1] for row in db.execute(
                    select(link_col, display_col_obj).where(link_col.in_(list(ids)))
                ).all()}
                for item in items:
                    val = item.get(col.name)
                    if val in mapping:
                        item[f"{col.name}_label"] = mapping[val]
            except Exception as e:
                logging.error(f"[Model] Failed to resolve labels for {cls.__tablename__}.{col.name}: {e}")

    @classmethod
    def resolve_m2m(cls, db: Session, items: List[dict]):
        """Fetches and attaches Many-to-Many associations for a list of items."""
        if not items: return
        m2m_defs = getattr(cls, "__m2m__", {})
        if not m2m_defs: return
        
        item_ids = [item["id"] for item in items if "id" in item]
        if not item_ids: return
        
        for field_name, defs in m2m_defs.items():
            bridge_table_name = defs.get("bridge_table")
            source_key = defs.get("source_key")
            target_key = defs.get("target_key")
            if not all([bridge_table_name, source_key, target_key]): continue
            
            try:
                bridge_table_obj = Table(bridge_table_name, cls.metadata, autoload_with=db.connection())
                query = select(bridge_table_obj.c[source_key], bridge_table_obj.c[target_key]).where(
                    bridge_table_obj.c[source_key].in_(item_ids)
                )
                rows = db.execute(query).all()
                mapping = {}
                for s_id, t_id in rows:
                    if s_id not in mapping: mapping[s_id] = []
                    mapping[s_id].append(t_id)
                for item in items:
                    item[field_name] = mapping.get(item["id"], [])
            except Exception as e:
                logging.error(f"[Model] Failed to resolve M2M for {cls.__tablename__}.{field_name}: {e}")
