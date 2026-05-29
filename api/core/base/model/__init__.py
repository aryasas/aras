"""
Purpose: Level 2 Base Model class for all data resources.
Context: Inherits from Aras (Level 1) and SQLAlchemy Base.
Impact: Provides generic CRUD, serialization, and metadata logic.
"""
import logging
from datetime import datetime, date, timezone
from typing import Any, Dict, List, Optional, Type, TypeVar, Tuple, Callable
from sqlalchemy import Column, Integer, Boolean, DateTime, func, String, select, or_, inspect, text, UniqueConstraint, Table, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session

from ..aras import Aras
from .queries import QueryMixin
from .hooks import HookMixin
from .serialization import SerializationMixin

class Base(DeclarativeBase):
    """Foundational SQLAlchemy Base."""
    __table_args__ = {'extend_existing': True}
    pass

T = TypeVar("T", bound="Model")

class Model(Aras, Base, QueryMixin, HookMixin, SerializationMixin):
    """
    Level 2 Core Model.
    Inherits from Aras (Level 1).
    Provides built-in ERP features and generic database operations.
    """
    __abstract__ = True
    _registry: Dict[str, Type['Model']] = {}
    _child_map: Dict[str, List[Dict[str, Optional[str]]]] = {} # Map parent_tablename -> [{resource, fk_column}]
    _actions: Dict[str, Any] = {} # Store registered model actions (Delayed Type)
    _computed: List[str] = [] # List of method names marked as computed fields

    @classmethod
    def _merge_inheritable_attributes(cls):
        """Merges inheritable class attributes from MRO."""
        for attr, default in (
            ("__features__", []),
            ("__scoped_by__", []),
            ("__unique_together__", []),
        ):
            merged: list = []
            seen: set = set()
            for base in cls.__mro__:
                vals = base.__dict__.get(attr, "_MISSING_")
                if vals == "_MISSING_": continue
                if vals is None: break 
                if not isinstance(vals, (list, tuple)): vals = [vals]
                for v in vals:
                    key = tuple(v) if isinstance(v, (list, tuple)) else v
                    if key in seen: continue
                    seen.add(key)
                    merged.append(v)
            if merged or attr in cls.__dict__:
                setattr(cls, attr, merged)

    @classmethod
    def _register_model_and_validate_inheritance(cls):
        """Registers the model and validates inheritance rules."""
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
            raise TypeError(f"{cls.__name__} inherits from multiple Level-3a abstract bases ({names}).")
        Model._registry[cls.__name__] = cls
        if hasattr(cls, "__tablename__"):
            Model._registry[cls.__tablename__] = cls

    @classmethod
    def _discover_child_relations(cls):
        """Auto-discovers child relations via FKs."""
        parent_table = getattr(cls, "__parent__", None)
        if parent_table:
            fk_column = None
            try:
                for col in cls.__table__.columns:
                    for fk in col.foreign_keys:
                        target_table = getattr(fk, "_column_tokens", [None])[1] if hasattr(fk, "_column_tokens") else fk.target_fullname.split('.')[0]
                        if target_table == parent_table:
                            fk_column = col.name
                            break
                    if fk_column: break
            except Exception:
                logging.error(f"Failed to determine FK column for child relation in {cls.__tablename__}.", exc_info=True)
                fk_column = None
            Model._child_map.setdefault(parent_table, [])
            if not any(c.get("resource") == cls.__tablename__ for c in Model._child_map[parent_table]):
                Model._child_map[parent_table].append({"resource": cls.__tablename__, "fk_column": fk_column})

    @classmethod
    def _discover_actions_and_computed_fields(cls):
        """Discovers and registers custom actions and computed properties."""
        from ...logic.model_actions import get_model_actions 
        cls._actions = get_model_actions(cls)
        computed = []
        for c in cls.__mro__:
            for name, descriptor in vars(c).items():
                if name in computed: continue
                if isinstance(descriptor, property):
                    if getattr(descriptor.fget, "_aras_computed", False): computed.append(name)
                elif callable(descriptor) and getattr(descriptor, "_aras_computed", False):
                    computed.append(name)
        cls._computed = computed

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._merge_inheritable_attributes()
        if not cls.__dict__.get("__abstract__"):
            cls._register_model_and_validate_inheritance()
            cls._discover_child_relations()
            cls._discover_actions_and_computed_fields()
        from ...logic.trait_injector import TraitInjector
        TraitInjector.inject(cls)
        if not cls.__dict__.get("__abstract__") and hasattr(cls, "__table__"):
            cls._apply_unique_constraints()
    
    @classmethod
    def _apply_unique_constraints(cls):
        ut = getattr(cls, "__unique_together__", None) or []
        if ut:
            tablename = cls.__tablename__
            for cols in ut:
                cols = tuple(cols)
                name = f"uq_{tablename}_{'_'.join(cols)}"
                existing = {c.name for c in cls.__table__.constraints if c.name}
                if name in existing: continue
                try: cls.__table__.append_constraint(UniqueConstraint(*cols, name=name))
                except Exception as e: logging.warning(f"[Model] UniqueConstraint application skipped: {e}")

    __soft_delete__: bool = False
    __serialize_relations__: dict = {}
    __display_fields__: tuple = ()
    __parent__: str = None 
    __m2m__: dict = {}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(default=func.now(), onupdate=func.now(), server_default=func.now())
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    _SKIP   = frozenset({"id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at"})
    _SYSTEM = frozenset({"id", "created_at", "updated_at", "deleted_at", "created_by", "updated_by"})

    @classmethod
    def get(cls: Type[T], db: Session, item_id) -> Optional[T]:
        return db.get(cls, item_id)

    @classmethod
    def get_model(cls, key: str) -> Type['Model']:
        model = cls._registry.get(key)
        if model is None: raise KeyError(f"No model registered for key: {key!r}")
        return model

    def save(self, db: Session, data: dict = None, *, user_id: int = None, is_new: bool = None):
        if is_new is None: is_new = not inspect(self).persistent
        skip = self._SKIP if is_new else (self._SKIP - {"updated_by"})
        if data:
            for col in self.__table__.columns:
                if col.name not in skip and col.name in data:
                    val = data[col.name]
                    if val is None and not col.nullable and getattr(self, col.name) is not None: continue
                    setattr(self, col.name, val)
        if user_id:
            if is_new: self.created_by = user_id
            self.updated_by = user_id

        # ── Series Generation ──
        if is_new:
            try:
                from ...service_registry import ServiceRegistry
                FieldModel = ServiceRegistry.get("FieldModel")
                ResourceModel = ServiceRegistry.get("ResourceModel")
                SeriesManager = ServiceRegistry.get("SeriesManager")
                if ResourceModel and FieldModel and SeriesManager:
                    res_rec = db.query(ResourceModel).filter(ResourceModel.name == self.__tablename__).first()
                    if res_rec:
                        fields_with_series = db.query(FieldModel).filter(FieldModel.resource_id == res_rec.id, FieldModel.series.isnot(None), FieldModel.series != "").all()
                        for f_meta in fields_with_series:
                            if not getattr(self, f_meta.name, None):
                                series_key = f"{self.__tablename__}_{f_meta.name}"
                                generated = SeriesManager.get_next(db, key=series_key, default_prefix=f_meta.series)
                                setattr(self, f_meta.name, generated)
            except Exception as e: logging.error(f"[Model] Series generation failed: {e}")

        # ── Parent Fallback ──
        parent_table = getattr(self.__class__, "__parent__", None)
        if is_new and parent_table:
            parent_fk_col = next((c for c in self.__table__.columns if c.foreign_keys and next(iter(c.foreign_keys)).column.table.name == parent_table), None)
            if parent_fk_col:
                parent_id = getattr(self, parent_fk_col.name, None)
                if parent_id:
                    parent_cls = Model._registry.get(parent_table)
                    if parent_cls:
                        parent_obj = db.get(parent_cls, parent_id)
                        parent_name = getattr(parent_obj, "name", None) if parent_obj else None
                        if parent_name:
                            if not getattr(self, "name", None): setattr(self, "name", parent_name)
                            if not getattr(self, "code", None): setattr(self, "code", parent_name)

        if not getattr(self, "code", None):
            name_val = getattr(self, "name", None)
            if name_val: setattr(self, "code", name_val)

        self.before_save(is_new=is_new, db=db)
        if is_new: db.add(self)
        db.flush() 
        if data: self.save_m2m(db, data)
        db.refresh(self)
        self.after_save(is_new=is_new)
        self._fire_hooks("on_create" if is_new else "on_update")
        db.flush()
        return self

    def save_m2m(self, db: Session, data: dict):
        m2m_defs = getattr(self, "__m2m__", {})
        for field_name, defs in m2m_defs.items():
            if field_name not in data: continue
            new_ids = data[field_name]
            if not isinstance(new_ids, list): continue
            bridge_table = defs.get("bridge_table")
            source_key = defs.get("source_key")
            target_key = defs.get("target_key")
            if not all([bridge_table, source_key, target_key]): continue
            try:
                bridge_table_obj = Table(bridge_table, self.metadata, autoload_with=db.connection())
                db.execute(bridge_table_obj.delete().where(bridge_table_obj.c[source_key] == self.id))
                if new_ids:
                    insert_values = [{source_key: self.id, target_key: t_id} for t_id in new_ids if t_id is not None]
                    if insert_values: db.execute(bridge_table_obj.insert().values(insert_values))
            except Exception as e:
                db.rollback()
                raise e

    @classmethod
    def find(cls: Type[T], db: Session, **kwargs) -> Optional[T]:
        return db.scalar(select(cls).filter_by(**kwargs).limit(1))

    @classmethod
    def get_or_create(cls: Type[T], db: Session, defaults: dict = None, user_id: int = None, **lookup) -> Tuple[T, bool]:
        obj = cls.find(db, **lookup)
        if obj: return obj, False
        data = {**lookup, **(defaults or {})}
        return cls.create(db, data, user_id=user_id), True

    @classmethod
    def create(cls: Type[T], db: Session, data: dict, user_id: int = None) -> T:
        return cls().save(db, data, user_id=user_id, is_new=True)

    def update_self(self, db: Session, data: dict, user_id: int = None):
        return self.save(db, data, user_id=user_id, is_new=False)

    def delete_self(self, db: Session, user_id: int = None):
        self._fire_hooks("on_delete")
        if self.__soft_delete__ and self.deleted_at is None:
            self.deleted_at = datetime.now(timezone.utc)
            if user_id: self.updated_by = user_id
        else: db.delete(self)

    def __repr__(self): return f"<{self.__class__.__name__} id={getattr(self, 'id', '?')}>"

class SoftModel(Model):
    __abstract__ = True
    __soft_delete__ = True
