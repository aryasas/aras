"""
Purpose: Level 2 Base Model class for all data resources.
Context: Inherits from Aras (Level 1) and SQLAlchemy Base.
Impact: Provides generic CRUD, serialization, and metadata logic.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar, Tuple
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, func, String, select, or_, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from decimal import Decimal
from enum import Enum

from .aras import Aras

class Base(DeclarativeBase):
    """Foundational SQLAlchemy Base."""
    pass

T = TypeVar("T", bound="Model")

class Model(Aras, Base):
    """
    Level 2 Core Model.
    Inherits from Aras (Level 1).
    Provides built-in ERP features and generic database operations.
    """
    __abstract__ = True
    _registry: Dict[str, Type['Model']] = {}
    _child_map: Dict[str, List[str]] = {} # Map parent_tablename -> [child_tablenames]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 1. Automatically register non-abstract subclasses
        if not cls.__dict__.get("__abstract__"):
            Model._registry[cls.__name__] = cls
            
            # 2. Handle Parent-Child Auto Discovery
            parent_table = getattr(cls, "__parent__", None)
            if parent_table:
                if parent_table not in Model._child_map:
                    Model._child_map[parent_table] = []
                if cls.__tablename__ not in Model._child_map[parent_table]:
                    Model._child_map[parent_table].append(cls.__tablename__)

        # 3. Inject Generic Features (Traits)
        from ..lib.trait_injector import TraitInjector
        TraitInjector.inject(cls)

    __soft_delete__: bool = False
    __serialize_relations__: dict = {}
    __display_fields__: tuple = ()
    __parent__: str = None # Tablename of the parent model

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now()
    )
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def before_save(self, is_new: bool): 
        """Generic hook executed before database commit."""
        pass
        
    def after_save(self, is_new: bool): 
        """Generic hook executed after database commit."""
        pass

    # ── Internal Helpers ──────────────────────────────────────────────────────

    _SKIP   = frozenset({"id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at"})
    _SYSTEM = frozenset({"id", "created_at", "updated_at", "deleted_at", "created_by", "updated_by", "is_active"})

    @classmethod
    def _q(cls, active_only=False):
        """Standardized query builder with soft-delete support."""
        stmt = select(cls)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(cls.is_active == True)
        return stmt

    @classmethod
    def apply_filters(cls, stmt, filters: List[dict] = None):
        """
        Apply advanced filters with operators.
        filters = [{"field": "name", "op": "ilike", "value": "john"}]
        """
        if not filters:
            return stmt
            
        for f in filters:
            field = f.get("field")
            op = f.get("op", "=")
            val = f.get("value")
            
            if not field or not hasattr(cls, field): continue
            col = getattr(cls, field)
            
            try:
                if op == "=": stmt = stmt.where(col == val)
                elif op == "!=": stmt = stmt.where(col != val)
                elif op == ">": stmt = stmt.where(col > val)
                elif op == ">=": stmt = stmt.where(col >= val)
                elif op == "<": stmt = stmt.where(col < val)
                elif op == "<=": stmt = stmt.where(col <= val)
                elif op == "ilike": stmt = stmt.where(col.ilike(f"%{val}%"))
                elif op == "between" and isinstance(val, list) and len(val) == 2:
                    stmt = stmt.where(col.between(val[0], val[1]))
                elif op == "in" and isinstance(val, list):
                    stmt = stmt.where(col.in_(val))
            except Exception:
                continue
        return stmt

    @classmethod
    def apply_search(cls, stmt, term: str = None, fields: list = None):
        """Apply global search across specified fields."""
        if not term:
            return stmt
            
        search_fields = fields or list(cls.__display_fields__)
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

    # ── Generic CRUD ──────────────────────────────────────────────────────────

    @classmethod
    def fetch(cls: Type[T], db: Session, item_id=None, *, active_only=False) -> Any:
        """Fetches a single record by ID or all records if ID is None."""
        if item_id is not None:
            return db.get(cls, item_id)
        return db.scalars(cls._q(active_only).order_by(cls.id.desc())).all()

    @classmethod
    def get(cls: Type[T], db: Session, item_id) -> Optional[T]:
        return db.get(cls, item_id)

    @classmethod
    def paginate(cls: Type[T], db: Session, page: int = 1, per_page: int = 20, 
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

        return {
            "items": results,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page if per_page > 0 else 1
        }

    @classmethod
    def resolve_labels(cls, db: Session, items: List[dict]):
        """Automatically fetches human-readable labels for foreign key columns."""
        if not items: return
        
        for col in cls.__table__.columns:
            display_col = col.info.get("display_column")
            if not display_col: continue
            
            # Detect target table from ForeignKey
            target_table = None
            if col.foreign_keys:
                for fk in col.foreign_keys:
                    target_table = fk.column.table.name
                    break
            
            if not target_table: continue
            
            # Collect unique IDs to fetch from target table
            ids = {item[col.name] for item in items if item.get(col.name) is not None}
            if not ids: continue
            
            # Fetch mapping from target table using low-level metadata to avoid circular imports
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
                # Log error or silently skip if target column doesn't exist/query fails
                print(f"[Model] Warning: Failed to resolve labels for {cls.__tablename__}.{col.name}: {e}")

    def save(self, db: Session, data: dict = None, *, user_id: int = None, is_new: bool = None):
        """Unified create/update logic with audit tracking and hooks."""
        if is_new is None:
            is_new = not inspect(self).persistent

        skip = self._SKIP if is_new else (self._SKIP - {"updated_by"})
        if data:
            for col in self.__table__.columns:
                if col.name not in skip and col.name in data:
                    setattr(self, col.name, data[col.name])

        if user_id:
            if is_new:
                self.created_by = user_id
            self.updated_by = user_id

        self.before_save(is_new=is_new)
        if is_new:
            db.add(self)

        db.commit()
        db.refresh(self)
        self.after_save(is_new=is_new)
        return self

    @classmethod
    def create(cls: Type[T], db: Session, data: dict, user_id: int = None) -> T:
        return cls().save(db, data, user_id=user_id, is_new=True)

    def update_self(self, db: Session, data: dict, user_id: int = None):
        return self.save(db, data, user_id=user_id, is_new=False)

    def delete_self(self, db: Session, user_id: int = None):
        if self.__soft_delete__ and self.deleted_at is None:
            self.deleted_at = datetime.now(timezone.utc)
            if user_id:
                self.updated_by = user_id
            db.commit()
        else:
            db.delete(self)
            db.commit()

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self, include: list = None, exclude: list = None) -> dict:
        """Generic serialization into a dictionary, respecting metadata flags."""
        excl = set(exclude or [])
        incl = set(include) if include else None
        result = {}
        for col in self.__table__.columns:
            if incl and col.name not in incl: continue
            if col.name in excl: continue
            if col.info.get("hidden", False) and (not incl or col.name not in incl):
                continue

            val = getattr(self, col.name, None)
            if isinstance(val, (datetime, date)): result[col.name] = val.isoformat()
            elif isinstance(val, Decimal): result[col.name] = float(val)
            elif isinstance(val, Enum): result[col.name] = val.value
            else: result[col.name] = val
            
        for out_key, (rel_attr, rel_field) in (self.__serialize_relations__ or {}).items():
            if incl and out_key not in incl: continue
            if out_key in excl: continue
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None
        return result

    @classmethod
    def get_ui_metadata(cls, translations: Dict[str, str] = None) -> Dict[str, Any]:
        """Generates metadata for automatic UI form/list generation."""
        fields = []
        translations = translations or {}
        
        for column in cls.__table__.columns:
            if column.name in cls._SYSTEM: continue
            
            # Detect Foreign Key (Lookup)
            target_resource = None
            ui_type = column.info.get("ui_type")
            
            if column.foreign_keys:
                # Basic FK detection
                target_resource = list(column.foreign_keys)[0].column.table.name
                if not ui_type:
                    ui_type = "lookup"
            
            if not ui_type:
                # Map SQLAlchemy types to UI types
                from sqlalchemy import String, Integer, Boolean, DateTime, Date, Numeric
                col_type = column.type
                if isinstance(col_type, String): ui_type = "string"
                elif isinstance(col_type, (Integer, Numeric)): ui_type = "number"
                elif isinstance(col_type, Boolean): ui_type = "boolean"
                elif isinstance(col_type, DateTime): ui_type = "datetime"
                elif isinstance(col_type, Date): ui_type = "date"
                else: ui_type = "string"

            # Apply Translation if available
            label = translations.get(f"field.{column.name}.label") or column.info.get("label", column.name.replace("_id", "").replace("_", " ").title())

            field_info = {
                "name": column.name,
                "label": label,
                "type": ui_type,
                "required": not column.nullable,
                "target": target_resource,
                "hidden": column.info.get("hidden", False)
            }
            fields.append(field_info)

        return {
            "resource": cls.__tablename__,
            "title": translations.get("resource.title") or getattr(cls, "__title__", cls.__tablename__.replace("_", " ").title()),
            "fields": fields,
            "children": cls._child_map.get(cls.__tablename__, []),
            "workflow": getattr(cls, "__workflow__", None),
        }

    def __repr__(self):
        return f"<{self.__class__.__name__} id={getattr(self, 'id', '?')}>"

class SoftModel(Model):
    """Level 2 Core Model with enabled Soft-Delete trait."""
    __abstract__ = True
    __soft_delete__ = True
