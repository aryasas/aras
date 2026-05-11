from typing import Any, Dict, List, Optional, Type, TypeVar, Tuple
from datetime import datetime, date, timezone
from sqlalchemy import Column, Integer, Boolean, DateTime, func, String, select, or_, inspect, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from .aras import Aras
from decimal import Decimal
from enum import Enum
import json

class Base(DeclarativeBase):
    pass

T = TypeVar("T", bound="ArasModel")

class ArasModel(Base, Aras):
    __abstract__ = True

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

    def before_save(self, is_new: bool): pass
    def after_save(self, is_new: bool): pass

    # ── Internal sets ─────────────────────────────────────────────────────────

    _SKIP   = frozenset({"id", "created_at", "updated_at", "created_by", "updated_by", "deleted_at"})
    _SYSTEM = frozenset({"id", "created_at", "updated_at", "deleted_at",
                         "created_by", "updated_by", "is_active"})

    # ── Base query builder (internal) ─────────────────────────────────────────

    @classmethod
    def _q(cls, active_only=False):
        """Return a base select statement with soft-delete and optional active filter applied."""
        stmt = select(cls)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(cls.is_active == True)
        return stmt

    # ── Single-row fetchers ───────────────────────────────────────────────────

    @classmethod
    def fetch(cls: Type[T], db: Session, item_id=None, *, active_only=False) -> Any:
        """
        fetch(id)  → single row by PK
        fetch()    → list of all rows
        """
        if item_id is not None:
            return db.get(cls, item_id)
        return db.scalars(cls._q(active_only).order_by(cls.id.desc())).all()

    @classmethod
    def get(cls: Type[T], db: Session, item_id) -> Optional[T]:
        return db.get(cls, item_id)

    @classmethod
    def find(cls: Type[T], db: Session, **kwargs) -> Optional[T]:
        """Return first row matching keyword filters, or None."""
        stmt = cls._q().filter_by(**kwargs)
        return db.scalars(stmt).first()

    @classmethod
    def find_all(cls: Type[T], db: Session, **kwargs) -> List[T]:
        """Return all rows matching keyword filters."""
        stmt = cls._q().filter_by(**kwargs).order_by(cls.id.desc())
        return list(db.scalars(stmt).all())

    @classmethod
    def exists(cls, db: Session, **kwargs) -> bool:
        """True if any row matches the given filters."""
        return cls.find(db, **kwargs) is not None

    @classmethod
    def count(cls, db: Session, **kwargs) -> int:
        """Count rows, with optional keyword filters."""
        stmt = select(func.count()).select_from(cls)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if kwargs:
            stmt = stmt.filter_by(**kwargs)
        return db.scalar(stmt) or 0

    # ── List / pagination ─────────────────────────────────────────────────────

    @classmethod
    def list_all(cls: Type[T], db: Session, active_only=False) -> List[T]:
        return list(cls.fetch(db, active_only=active_only))

    @classmethod
    def paginate(cls: Type[T], db: Session, page: int = 1, per_page: int = 20, active_only=False, **filters):
        """
        Return items and total count for simple pagination.
        """
        stmt = cls._q(active_only)
        if filters:
            stmt = stmt.filter_by(**filters)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = db.scalars(stmt.order_by(cls.id.desc()).offset((page - 1) * per_page).limit(per_page)).all()

        return {
            "items": list(items),
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }

    @classmethod
    def latest(cls: Type[T], db: Session, active_only=False) -> Optional[T]:
        """Return the single most recently created row."""
        return db.scalars(cls._q(active_only).order_by(cls.id.desc())).first()

    @classmethod
    def oldest(cls: Type[T], db: Session, active_only=False) -> Optional[T]:
        return db.scalars(cls._q(active_only).order_by(cls.id.asc())).first()

    @classmethod
    def first_n(cls: Type[T], db: Session, n: int, active_only=False, **filters) -> List[T]:
        """Return the first n rows (newest first)."""
        stmt = cls._q(active_only)
        if filters:
            stmt = stmt.filter_by(**filters)
        return list(db.scalars(stmt.order_by(cls.id.desc()).limit(n)).all())

    @classmethod
    def between(cls, db: Session, field: str, start, end, active_only=False):
        """Return rows where field is between start and end (inclusive)."""
        col = getattr(cls, field)
        return list(db.scalars(cls._q(active_only).where(col.between(start, end)).order_by(cls.id.desc())).all())

    @classmethod
    def order_by_field(cls, db: Session, field: str, desc: bool = True, active_only=False):
        col = getattr(cls, field)
        stmt = cls._q(active_only)
        return list(db.scalars(stmt.order_by(col.desc() if desc else col.asc())).all())

    @classmethod
    def ids(cls, db: Session, **filters) -> list:
        """Return a flat list of PKs matching filters."""
        stmt = select(cls.id)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return list(db.scalars(stmt).all())

    @classmethod
    def pluck(cls, db: Session, field: str, **filters) -> list:
        """Return a flat list of values for a single field."""
        col = getattr(cls, field)
        stmt = select(col)
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return list(db.scalars(stmt).all())

    @classmethod
    def as_choices(cls, db: Session, value_field: str = "id", label_field: str = None, active_only=True):
        """
        Return [(value, label), ...] tuples for use in select fields.
        """
        lf = label_field or (cls.__display_fields__[0] if cls.__display_fields__ else "name")
        stmt = cls._q(active_only).order_by(cls.id.asc())
        rows = db.scalars(stmt).all()
        return [(getattr(r, value_field), getattr(r, lf, str(r.id))) for r in rows]

    # ── Aggregates ────────────────────────────────────────────────────────────

    @classmethod
    def sum(cls, db: Session, field: str, **filters):
        col = getattr(cls, field)
        stmt = select(func.sum(col))
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return db.scalar(stmt) or 0

    @classmethod
    def avg(cls, db: Session, field: str, **filters):
        col = getattr(cls, field)
        stmt = select(func.avg(col))
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return db.scalar(stmt)

    @classmethod
    def max_val(cls, db: Session, field: str, **filters):
        col = getattr(cls, field)
        stmt = select(func.max(col))
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return db.scalar(stmt)

    @classmethod
    def min_val(cls, db: Session, field: str, **filters):
        col = getattr(cls, field)
        stmt = select(func.min(col))
        if cls.__soft_delete__:
            stmt = stmt.where(cls.deleted_at.is_(None))
        if filters:
            stmt = stmt.filter_by(**filters)
        return db.scalar(stmt)

    # ── Metadata ──────────────────────────────────────────────────────────────

    @classmethod
    def column_names(cls) -> list:
        """Return list of all column names on this model."""
        return [c.name for c in cls.__table__.columns]

    @classmethod
    def column_names_public(cls) -> list:
        """Column names excluding system fields."""
        return [c.name for c in cls.__table__.columns if c.name not in cls._SYSTEM]

    def __repr__(self):
        return f"<{self.__class__.__name__} id={getattr(self, 'id', '?')}>"

    @classmethod
    def search(cls, db: Session, term: str, fields: list = None):
        """
        Simple ILIKE search across given fields (or __display_fields__).
        """
        cols = fields or list(cls.__display_fields__)
        if not cols:
            return []
        conditions = [
            getattr(cls, f).ilike(f"%{term}%")
            for f in cols if hasattr(cls, f)
        ]
        if not conditions:
            return []
        return list(db.scalars(cls._q().where(or_(*conditions)).order_by(cls.id.desc())).all())

    # ── Write ─────────────────────────────────────────────────────────────────

    def save(self, db: Session, data: dict = None, *, user_id: int = None, is_new: bool = None):
        """Unified create/update."""
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
    def create(cls, db: Session, data: dict, user_id: int = None):
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
        excl = set(exclude or [])
        incl = set(include) if include else None
        result = {}
        for col in self.__table__.columns:
            if incl and col.name not in incl: continue
            if col.name in excl: continue
            
            # Security: Skip hidden columns unless explicitly included
            if col.info.get("hidden", False) and (not incl or col.name not in incl):
                continue

            val = getattr(self, col.name, None)
            if isinstance(val, datetime): result[col.name] = val.isoformat()
            elif isinstance(val, date): result[col.name] = val.isoformat()
            elif isinstance(val, Decimal): result[col.name] = float(val)
            elif isinstance(val, Enum): result[col.name] = val.value
            else: result[col.name] = val

        for out_key, (rel_attr, rel_field) in (self.__serialize_relations__ or {}).items():
            if incl and out_key not in incl: continue
            if out_key in excl: continue
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None
        return result

    def to_json(self) -> dict:
        return self.to_dict()

    @classmethod
    def get_ui_metadata(cls) -> Dict[str, Any]:
        fields = []
        for column in cls.__table__.columns:
            if column.name in ['id', 'created_at', 'updated_at', 'deleted_at', 'created_by', 'updated_by']:
                continue

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
            "fields": fields,
            "workflow": getattr(cls, "__workflow__", None),
        }

class ArasSoftModel(ArasModel):
    __abstract__ = True
    __soft_delete__ = True

def ArasColumn(*args, label: str = None, ui_type: str = "string", read_only: bool = False, hidden: bool = False, searchable: bool = True, **kwargs):
    if "info" not in kwargs:
        kwargs["info"] = {}

    kwargs["info"].update({
        "label": label,
        "ui_type": ui_type,
        "read_only": read_only,
        "hidden": hidden,
        "searchable": searchable
    })
    return mapped_column(*args, **kwargs)
