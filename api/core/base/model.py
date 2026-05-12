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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # 1. Automatically register non-abstract subclasses
        if not cls.__dict__.get("__abstract__"):
            Model._registry[cls.__name__] = cls
            
        # 2. Inject Generic Features (Traits)
        from ..lib.trait_injector import TraitInjector
        TraitInjector.inject(cls)

    __soft_delete__: bool = False
    __serialize_relations__: dict = {}
    __display_fields__: tuple = ()

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

    # ── Generic CRUD ──────────────────────────────────────────────────────────

    @classmethod
    def fetch(cls: Type[T], db: Session, item_id=None, *, active_only=False) -> Any:
        """Fetches a single record by ID or all records if ID is None."""
        if item_id is not None:
            return db.get(cls, item_id)
        return db.scalars(cls._q(active_only).order_by(cls.id.desc())).all()

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
        return result

    @classmethod
    def get_ui_metadata(cls) -> Dict[str, Any]:
        """Generates metadata for automatic UI form/list generation."""
        fields = []
        for column in cls.__table__.columns:
            if column.name in cls._SYSTEM: continue
            field_info = {
                "name": column.name,
                "label": column.info.get("label", column.name.replace("_", " ").title()),
                "type": column.info.get("ui_type", "string"),
                "required": not column.nullable,
                "read_only": column.info.get("read_only", False),
                "hidden": column.info.get("hidden", False),
                "searchable": column.info.get("searchable", True),
            }
            fields.append(field_info)
        return {
            "resource": cls.__tablename__,
            "title": getattr(cls, "__title__", cls.__tablename__.replace("_", " ").title()),
            "fields": fields
        }

class SoftModel(Model):
    """Level 2 Core Model with enabled Soft-Delete trait."""
    __abstract__ = True
    __soft_delete__ = True
