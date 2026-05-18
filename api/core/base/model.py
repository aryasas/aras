"""
Purpose: Level 2 Base Model class for all data resources.
Context: Inherits from Aras (Level 1) and SQLAlchemy Base.
Impact: Provides generic CRUD, serialization, and metadata logic.
"""
from typing import Any, Dict, List, Optional, Type, TypeVar, Tuple, Callable
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, func, String, select, or_, inspect, text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from decimal import Decimal
from enum import Enum
import logging

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
    _child_map: Dict[str, List[Dict[str, Optional[str]]]] = {} # Map parent_tablename -> [{resource, fk_column}]
    _actions: Dict[str, 'ModelAction'] = {} # Store registered model actions (Delayed Type)
    _computed: List[str] = [] # List of method names marked as computed fields

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        # 0. Merge inheritable class attributes from MRO so concrete subclasses
        #    pick up __features__, __scoped_by__, __unique_together__
        #    from any abstract base (DocumentBase, MasterDataBase, ...) without
        #    losing the child's own values. Child wins on conflict by appearing first.
        for attr, default in (
            ("__features__", []),
            ("__scoped_by__", []),
            ("__unique_together__", []),
        ):
            merged: list = []
            seen: set = set()
            for base in cls.__mro__:
                # Use a marker to distinguish between 'missing' and 'falsy' (like [])
                vals = base.__dict__.get(attr, "_MISSING_")
                if vals == "_MISSING_":
                    continue

                # If the child explicitly defines it as None, it means "clear all inheritance"
                if vals is None:
                    break 

                if not isinstance(vals, (list, tuple)):
                    vals = [vals]
                for v in vals:
                    key = tuple(v) if isinstance(v, (list, tuple)) else v
                    if key in seen:
                        continue
                    seen.add(key)
                    merged.append(v)
            if merged or attr in cls.__dict__:
                setattr(cls, attr, merged)

        # 1. Automatically register non-abstract subclasses
        if not cls.__dict__.get("__abstract__"):
            # Three-layer inheritance validation: a concrete model may inherit at
            # most one Level-3a abstract base (DocumentBase OR LineItemBase, etc.).
            # We filter to only 'leaf' abstract bases to allow multi-level abstract 
            # inheritance (e.g. MasterDataBase -> ErpBase -> Model).
            all_abstract_bases = [
                b for b in cls.__mro__[1:]
                if isinstance(b, type) and issubclass(b, Model) and b is not Model
                and b.__dict__.get("__abstract__") is True
            ]
            leaf_abstract_bases = [
                b for b in all_abstract_bases
                if not any(issubclass(other, b) for other in all_abstract_bases if other is not b)
            ]
            if len(leaf_abstract_bases) > 1:
                names = ", ".join(b.__name__ for b in leaf_abstract_bases)
                raise TypeError(
                    f"{cls.__name__} inherits from multiple Level-3a abstract bases ({names}). "
                    f"Pick exactly one (DocumentBase | LineItemBase | MasterDataBase | ConfigBase)."
                )

            # Register by class name AND tablename
            Model._registry[cls.__name__] = cls
            if hasattr(cls, "__tablename__"):
                Model._registry[cls.__tablename__] = cls

            # 2. Handle Parent-Child Auto Discovery
            parent_table = getattr(cls, "__parent__", None)
            if parent_table:
                # Detect which local column FKs to the parent table (defer until columns exist)
                fk_column = None
                try:
                    for col in cls.__table__.columns:
                        for fk in col.foreign_keys:
                            target_table = getattr(fk, "_column_tokens", [None])[1] if hasattr(fk, "_column_tokens") else fk.target_fullname.split('.')[0]
                            if target_table == parent_table:
                                fk_column = col.name
                                break
                        if fk_column:
                            break
                except Exception as e:
                    import traceback
                    print(f"Error determining fk_column for {cls.__tablename__}: {e}")
                    traceback.print_exc()
                    fk_column = None

                Model._child_map.setdefault(parent_table, [])
                if not any(c.get("resource") == cls.__tablename__ for c in Model._child_map[parent_table]):
                    Model._child_map[parent_table].append({
                        "resource": cls.__tablename__,
                        "fk_column": fk_column,
                    })

            # 3. Discover and register custom actions
            from ..logic.model_actions import get_model_actions # Delayed import
            cls._actions = get_model_actions(cls)

            # 4. Discover computed properties
            computed = []
            for c in cls.__mro__:
                for name, descriptor in vars(c).items():
                    if name in computed:
                        continue
                    if isinstance(descriptor, property):
                        if getattr(descriptor.fget, "_aras_computed", False):
                            computed.append(name)
                    elif callable(descriptor) and getattr(descriptor, "_aras_computed", False):
                        computed.append(name)
            cls._computed = computed

        # 5. Inject Generic Features (Traits)
        from ..logic.trait_injector import TraitInjector
        TraitInjector.inject(cls)

        # 6. Apply __unique_together__ as composite UniqueConstraints. Only for
        #    concrete (mapped) models — abstract bases have no __table__.
        if not cls.__dict__.get("__abstract__") and hasattr(cls, "__table__"):
            ut = getattr(cls, "__unique_together__", None) or []
            if ut:
                tablename = cls.__tablename__
                for cols in ut:
                    cols = tuple(cols)
                    name = f"uq_{tablename}_{'_'.join(cols)}"
                    # Skip if already present (sync re-import safety)
                    existing = {c.name for c in cls.__table__.constraints if c.name}
                    if name in existing:
                        continue
                    try:
                        cls.__table__.append_constraint(UniqueConstraint(*cols, name=name))
                    except Exception as e:
                        print(f"[Model] __unique_together__ skipped for {tablename}{cols}: {e}")

    __soft_delete__: bool = False
    __serialize_relations__: dict = {}
    __display_fields__: tuple = ()
    __parent__: str = None # Tablename of the parent model
    __m2m__: dict = {} # Many-to-Many relationship definitions

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    _SYSTEM = frozenset({"id", "created_at", "updated_at", "deleted_at", "created_by", "updated_by"})

    @classmethod
    def _q(cls, active_only=False):
        """Standardized query builder with soft-delete support."""
        stmt = select(cls)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        # is_active is now opt-in (activatable trait); only filter if column exists.
        if active_only and hasattr(cls, "is_active"):
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
                elif op == "shared_scope" and isinstance(val, dict):
                    direct_id = val["direct"]
                    other_ids = val["others"]
                    col_obj = getattr(cls, field)
                    is_shared_col = getattr(cls, "is_shared", None)
                    if is_shared_col is not None and other_ids:
                        from sqlalchemy import or_
                        stmt = stmt.where(
                            or_(
                                col_obj == direct_id,
                                (col_obj.in_(other_ids)) & (is_shared_col == True)
                            )
                        )
                    else:
                        stmt = stmt.where(col_obj == direct_id)
            except Exception as e:
                logging.warning("serialization skipped: %s", e)
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
            item = db.get(cls, item_id)
            if item:
                res = item.to_dict()
                cls.resolve_labels(db, [res])
                cls.resolve_m2m(db, [res])
                return res
            return None
        items = db.scalars(cls._q(active_only).order_by(cls.id.desc())).all()
        results = [item.to_dict() for item in items]
        cls.resolve_labels(db, results)
        cls.resolve_m2m(db, results)
        return results

    @classmethod
    def get(cls: Type[T], db: Session, item_id) -> Optional[T]:
        return db.get(cls, item_id)

    @classmethod
    def get_model(cls, key: str) -> Type['Model']:
        """Look up a registered model by class name or __tablename__. Raises KeyError if not found."""
        model = cls._registry.get(key)
        if model is None:
            raise KeyError(f"No model registered for key: {key!r}")
        return model

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

        # Resolve choices fields — convert raw value to human-readable label
        for col in cls.__table__.columns:
            choices = col.info.get("choices")
            if not choices: continue
            label_map = {c: c.replace("_", " ").title() for c in choices}
            for item in items:
                val = item.get(col.name)
                if val in label_map:
                    item[f"{col.name}_label"] = label_map[val]

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
                print(f"[Model] Warning: Failed to resolve labels for {cls.__tablename__}.{col.name}: {e}")

        # Auto-resolve remaining FK columns that still lack a _label
        already_resolved = {f"{col.name}_label" for col in cls.__table__.columns if col.info.get("display_column")}
        for col in cls.__table__.columns:
            if not col.foreign_keys: continue
            if col.info.get("display_column"): continue
            col_label_key = f"{col.name}_label"
            if col_label_key in already_resolved: continue
            if items and col_label_key in items[0]: continue

            target_table = list(col.foreign_keys)[0].column.table.name
            table = cls.metadata.tables.get(target_table)
            if table is None: continue

            display_col_obj = None
            for candidate in ("name", "code", "title", "label"):
                if candidate in table.columns:
                    display_col_obj = table.columns[candidate]
                    break
            if display_col_obj is None: continue

            ids = {item[col.name] for item in items if item.get(col.name) is not None}
            if not ids: continue

            try:
                id_col = table.columns.get("id")
                if id_col is None: continue
                mapping = {row[0]: row[1] for row in db.execute(
                    select(id_col, display_col_obj).where(id_col.in_(list(ids)))
                ).all()}
                for item in items:
                    val = item.get(col.name)
                    if val in mapping:
                        item[col_label_key] = mapping[val]
            except Exception:
                pass

    @classmethod
    def resolve_m2m(cls, db: Session, items: List[dict]):
        """Fetches and attaches Many-to-Many associations for a list of items."""
        if not items: return
        m2m_defs = getattr(cls, "__m2m__", {})
        if not m2m_defs: return
        
        item_ids = [item["id"] for item in items if "id" in item]
        if not item_ids: return
        
        for field_name, defs in m2m_defs.items():
            bridge_table = defs.get("bridge_table")
            source_key = defs.get("source_key")
            target_key = defs.get("target_key")
            if not all([bridge_table, source_key, target_key]): continue
            
            try:
                # Use raw SQL to avoid requiring bridge models to be registered
                query = text(f"SELECT {source_key}, {target_key} FROM {bridge_table} WHERE {source_key} IN :ids")
                rows = db.execute(query, {"ids": tuple(item_ids)}).all()
                
                mapping = {}
                for s_id, t_id in rows:
                    if s_id not in mapping: mapping[s_id] = []
                    mapping[s_id].append(t_id)
                
                for item in items:
                    item[field_name] = mapping.get(item["id"], [])
            except Exception as e:
                print(f"[Model] Warning: Failed to resolve M2M for {cls.__tablename__}.{field_name}: {e}")

    def save(self, db: Session, data: dict = None, *, user_id: int = None, is_new: bool = None):
        """Unified create/update logic with audit tracking and hooks."""
        if is_new is None:
            is_new = not inspect(self).persistent

        skip = self._SKIP if is_new else (self._SKIP - {"updated_by"})
        if data:
            for col in self.__table__.columns:
                if col.name not in skip and col.name in data:
                    val = data[col.name]
                    # skip None for non-nullable columns that already have a value
                    if val is None and not col.nullable and getattr(self, col.name) is not None:
                        continue
                    setattr(self, col.name, val)

        if user_id:
            if is_new:
                self.created_by = user_id
            self.updated_by = user_id

        # ── Series Generation ──
        if is_new:
            try:
                # Use local imports to avoid circularity
                from ..registry.field_model import FieldModel
                from ..registry.resource_model import ResourceModel
                from ..manager.naming_manager import NamingManager
                
                # Check for fields with 'series' metadata in DB
                res_rec = db.query(ResourceModel).filter(ResourceModel.name == self.__tablename__).first()
                if res_rec:
                    fields_with_series = db.query(FieldModel).filter(
                        FieldModel.resource_id == res_rec.id,
                        FieldModel.series.isnot(None),
                        FieldModel.series != ""
                    ).all()
                    
                    for f_meta in fields_with_series:
                        current_val = getattr(self, f_meta.name, None)
                        if not current_val or current_val == "":
                            # Generate next value using NamingManager
                            # Key is resource_field for uniqueness
                            series_key = f"{self.__tablename__}_{f_meta.name}"
                            generated = NamingManager.get_next(db, key=series_key, default_prefix=f_meta.series)
                            setattr(self, f_meta.name, generated)
            except Exception as e:
                print(f"[Model] Series generation failed: {e}")

        # ── Code/name fallback for child rows: inherit from parent item name ──
        parent_table = getattr(self.__class__, "__parent__", None)
        if is_new and parent_table:
            parent_fk_col = next(
                (c for c in self.__table__.columns if c.foreign_keys and
                 next(iter(c.foreign_keys)).column.table.name == parent_table),
                None
            )
            if parent_fk_col is not None:
                parent_id = getattr(self, parent_fk_col.name, None)
                if parent_id:
                    parent_cls = Model._registry.get(parent_table)
                    if parent_cls:
                        parent_obj = db.get(parent_cls, parent_id)
                        parent_name = getattr(parent_obj, "name", None) if parent_obj else None
                        if parent_name:
                            if not getattr(self, "name", None):
                                setattr(self, "name", parent_name)
                            if not getattr(self, "code", None):
                                setattr(self, "code", parent_name)

        # ── Code fallback: if code is empty, use name ──
        if not getattr(self, "code", None):
            name_val = getattr(self, "name", None)
            if name_val:
                setattr(self, "code", name_val)

        self.before_save(is_new=is_new)
        if is_new:
            db.add(self)

        db.flush() # Ensure ID is available for M2M
        if data:
            self.save_m2m(db, data)
        
        db.refresh(self)
        self.after_save(is_new=is_new)
        self._fire_hooks("on_create" if is_new else "on_update")
        db.flush()
        return self

    def save_m2m(self, db: Session, data: dict):
        """Saves Many-to-Many associations from the provided data."""
        m2m_defs = getattr(self, "__m2m__", {})
        for field_name, defs in m2m_defs.items():
            if field_name not in data: continue
            
            new_ids = data[field_name]
            if not isinstance(new_ids, list): continue
            
            bridge_table = defs.get("bridge_table")
            source_key = defs.get("source_key")
            target_key = defs.get("target_key")
            if not all([bridge_table, source_key, target_key]): continue
            
            source_id = self.id
            try:
                # Clear existing
                db.execute(text(f"DELETE FROM {bridge_table} WHERE {source_key} = :s_id"), {"s_id": source_id})
                
                # Insert new
                for t_id in new_ids:
                    if t_id is not None:
                        db.execute(text(f"INSERT INTO {bridge_table} ({source_key}, {target_key}) VALUES (:s_id, :t_id)"), 
                                   {"s_id": source_id, "t_id": t_id})
            except Exception as e:
                print(f"[Model] Warning: Failed to save M2M for {self.__tablename__}.{field_name}: {e}")
                db.rollback()
                raise e

    @classmethod
    def find(cls: Type[T], db: Session, **kwargs) -> Optional[T]:
        """Return first row matching keyword filters, or None."""
        return db.scalar(select(cls).filter_by(**kwargs).limit(1))

    @classmethod
    def get_or_create(cls: Type[T], db: Session, defaults: dict = None, user_id: int = None, **lookup) -> Tuple[T, bool]:
        """
        Fetch first row matching lookup kwargs, or create it.
        Returns (instance, created: bool).
        """
        obj = cls.find(db, **lookup)
        if obj:
            return obj, False
        data = {**lookup, **(defaults or {})}
        return cls.create(db, data, user_id=user_id), True

    @classmethod
    def create(cls: Type[T], db: Session, data: dict, user_id: int = None) -> T:
        return cls().save(db, data, user_id=user_id, is_new=True)

    def update_self(self, db: Session, data: dict, user_id: int = None):
        return self.save(db, data, user_id=user_id, is_new=False)

    def _fire_hooks(self, hook_name: str):
        """Calls all methods on this instance decorated with @Aras.on_create/on_update/on_delete."""
        for name in dir(type(self)):
            method = getattr(type(self), name, None)
            if callable(method) and getattr(method, "_aras_hook", None) == hook_name:
                try:
                    getattr(self, name)()
                except Exception as e:
                    print(f"[Model] Hook error in {self.__tablename__}.{name}: {e}")

    def delete_self(self, db: Session, user_id: int = None):
        self._fire_hooks("on_delete")
        if self.__soft_delete__ and self.deleted_at is None:
            self.deleted_at = datetime.now(timezone.utc)
            if user_id:
                self.updated_by = user_id
        else:
            db.delete(self)

    # ── Serialization ─────────────────────────────────────────────────────────

    @classmethod
    def get_ui_metadata(cls):
        """Unified access to UI metadata, prioritizing Views and falling back to UIGenerator."""
        from .view import View
        from ..logic.ui_generator import UIGenerator
        
        view = View.get_for_model(cls)
        if view:
            return view.render_metadata()
        return UIGenerator.generate_metadata(cls)

    @staticmethod
    def computed_field(func: Callable) -> Callable:
        """Decorator to mark a method as a serializable computed field."""
        func._aras_computed = True
        return func

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

        # Include Computed Fields
        for name in self._computed:
            if incl and name not in incl: continue
            if name in excl: continue
            attr = getattr(self, name)
            val = attr() if callable(attr) else attr
            if isinstance(val, (datetime, date)): result[name] = val.isoformat()
            elif isinstance(val, Decimal): result[name] = float(val)
            else: result[name] = val

        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} id={getattr(self, 'id', '?')}>"

class SoftModel(Model):
    """Level 2 Core Model with enabled Soft-Delete trait."""
    __abstract__ = True
    __soft_delete__ = True
