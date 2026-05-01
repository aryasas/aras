# -*- coding: utf-8 -*-
from datetime import datetime, timezone
from arasCore.lib.core.extensions import db


def _now():
    return datetime.now(timezone.utc)


class ArasModel(db.Model):
    __abstract__ = True
    __soft_delete__: bool = False
    __serialize_relations__: dict = {}
    __display_fields__: tuple = ()

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=_now, server_default=db.func.now(), nullable=False)
    updated_at    = db.Column(db.DateTime, default=_now, onupdate=_now, server_default=db.func.now(), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    deleted_at = None

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def before_save(self, is_new: bool): pass
    def after_save(self, is_new: bool): pass

    # ── Internal sets ─────────────────────────────────────────────────────────

    _SKIP   = frozenset({"id", "created_at", "updated_at", "created_by_id", "updated_by_id", "deleted_at"})
    _SYSTEM = frozenset({"id", "created_at", "updated_at", "deleted_at",
                         "created_by_id", "updated_by_id", "is_active"})

    # ── Base query builder (internal) ─────────────────────────────────────────

    @classmethod
    def _q(cls, active_only=False):
        """Return a base query with soft-delete and optional active filter applied."""
        q = cls.query
        if cls.__soft_delete__:
            q = q.filter(cls.deleted_at.is_(None))
        if active_only:
            q = q.filter_by(is_active=True)
        return q

    # ── Single-row fetchers ───────────────────────────────────────────────────

    @classmethod
    def fetch(cls, item_id=None, *, active_only=False, or_404=False):
        """
        fetch(id)  → single row by PK (None or 404 if missing)
        fetch()    → list of all rows
        """
        if item_id is not None:
            obj = cls.query.get(item_id)
            if obj is None and or_404:
                from flask import abort
                abort(404)
            return obj
        return cls._q(active_only).order_by(cls.id.desc()).all()

    @classmethod
    def get(cls, item_id):
        return cls.fetch(item_id)

    @classmethod
    def get_or_404(cls, item_id):
        return cls.fetch(item_id, or_404=True)

    @classmethod
    def find(cls, **kwargs):
        """Return first row matching keyword filters, or None."""
        return cls._q().filter_by(**kwargs).first()

    @classmethod
    def find_or_404(cls, **kwargs):
        from flask import abort
        obj = cls.find(**kwargs)
        if obj is None:
            abort(404)
        return obj

    @classmethod
    def find_all(cls, **kwargs):
        """Return all rows matching keyword filters."""
        return cls._q().filter_by(**kwargs).order_by(cls.id.desc()).all()

    @classmethod
    def get_by(cls, field: str, value):
        """Return first row where field == value, or None."""
        return cls._q().filter(getattr(cls, field) == value).first()

    @classmethod
    def exists(cls, **kwargs) -> bool:
        """True if any row matches the given filters."""
        return cls._q().filter_by(**kwargs).first() is not None

    @classmethod
    def count(cls, **kwargs) -> int:
        """Count rows, with optional keyword filters."""
        q = cls._q()
        if kwargs:
            q = q.filter_by(**kwargs)
        return q.count()

    # ── List / pagination ─────────────────────────────────────────────────────

    @classmethod
    def list_all(cls, active_only=False):
        return cls.fetch(active_only=active_only)

    @classmethod
    def paginate(cls, page: int = 1, per_page: int = 20, active_only=False, **filters):
        """
        Return a SQLAlchemy Pagination object.
        Usage: paginate(page=2, per_page=50, status='open')
        """
        q = cls._q(active_only)
        if filters:
            q = q.filter_by(**filters)
        return q.order_by(cls.id.desc()).paginate(page=page, per_page=per_page, error_out=False)

    @classmethod
    def first_n(cls, n: int, active_only=False, **filters):
        """Return the first n rows (newest first)."""
        q = cls._q(active_only)
        if filters:
            q = q.filter_by(**filters)
        return q.order_by(cls.id.desc()).limit(n).all()

    @classmethod
    def latest(cls, active_only=False):
        """Return the single most recently created row."""
        return cls._q(active_only).order_by(cls.id.desc()).first()

    @classmethod
    def oldest(cls, active_only=False):
        return cls._q(active_only).order_by(cls.id.asc()).first()

    @classmethod
    def search(cls, term: str, fields: list = None):
        """
        Simple ILIKE search across given fields (or __display_fields__).
        Returns list of matching rows.
        """
        from sqlalchemy import or_
        cols = fields or list(cls.__display_fields__)
        if not cols:
            return []
        conditions = [
            getattr(cls, f).ilike(f"%{term}%")
            for f in cols if hasattr(cls, f)
        ]
        return cls._q().filter(or_(*conditions)).order_by(cls.id.desc()).all() if conditions else []

    @classmethod
    def order_by_field(cls, field: str, desc: bool = True, active_only=False):
        col = getattr(cls, field)
        q = cls._q(active_only)
        return q.order_by(col.desc() if desc else col.asc()).all()

    @classmethod
    def between(cls, field: str, start, end, active_only=False):
        """Return rows where field is between start and end (inclusive)."""
        col = getattr(cls, field)
        return cls._q(active_only).filter(col.between(start, end)).order_by(cls.id.desc()).all()

    @classmethod
    def ids(cls, **filters) -> list:
        """Return a flat list of PKs matching filters."""
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return [r.id for r in q.with_entities(cls.id).all()]

    @classmethod
    def pluck(cls, field: str, **filters) -> list:
        """Return a flat list of values for a single field."""
        col = getattr(cls, field)
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return [r[0] for r in q.with_entities(col).all()]

    @classmethod
    def as_choices(cls, value_field: str = "id", label_field: str = None, active_only=True):
        """
        Return [(value, label), ...] tuples for use in select fields.
        label_field defaults to first entry in __display_fields__, then 'name'.
        """
        lf = label_field or (cls.__display_fields__[0] if cls.__display_fields__ else "name")
        rows = cls._q(active_only).order_by(cls.id.asc()).all()
        return [(getattr(r, value_field), getattr(r, lf, str(r.id))) for r in rows]

    # ── Write ─────────────────────────────────────────────────────────────────

    @classmethod
    def form_columns(cls):
        from arasCore.lib.ui.label_utils import humanize
        from sqlalchemy import inspect as _sa_inspect
        try:
            cols = [attr.columns[0] for attr in _sa_inspect(cls).mapper.column_attrs]
        except Exception:
            cols = list(cls.__table__.columns)
        return [(humanize(c.name), c.name, c) for c in cols
                if c.name not in cls._SYSTEM and not c.primary_key]

    def save(self, data: dict = None, *, user_id: int = None, is_new: bool = None):
        """Unified create/update. Pass data dict to set fields; omit to commit current state."""
        if is_new is None:
            is_new = not db.inspect(self).persistent
        skip = self._SKIP if is_new else (self._SKIP - {"updated_by_id"})
        if data:
            for col in self.__table__.columns:
                if col.name not in skip and col.name in data:
                    setattr(self, col.name, data[col.name])
        if user_id:
            if is_new:
                self.created_by_id = user_id
            self.updated_by_id = user_id
        self.before_save(is_new=is_new)
        if is_new:
            db.session.add(self)
        db.session.commit()
        self.after_save(is_new=is_new)
        return self

    @classmethod
    def create(cls, data: dict, user_id: int = None):
        return cls().save(data, user_id=user_id, is_new=True)

    @classmethod
    def get_or_create(cls, defaults: dict = None, user_id: int = None, **lookup):
        """
        Fetch first row matching lookup kwargs, or create it.
        Returns (instance, created: bool).
        """
        obj = cls.find(**lookup)
        if obj:
            return obj, False
        data = {**lookup, **(defaults or {})}
        return cls.create(data, user_id=user_id), True

    def update_self(self, data: dict, user_id: int = None):
        return self.save(data, user_id=user_id, is_new=False)

    def set_field(self, field: str, value, user_id: int = None):
        """Update a single field and commit."""
        return self.save({field: value}, user_id=user_id, is_new=False)

    def toggle(self, field: str = "is_active", user_id: int = None):
        """Toggle a boolean field and commit."""
        current = getattr(self, field)
        return self.set_field(field, not current, user_id=user_id)

    def before_delete(self, user_id: int = None):
        """Override in subclasses for pre-delete side effects (no commit here)."""
        pass

    def delete_self(self, user_id: int = None):
        self.before_delete(user_id=user_id)
        if self.__soft_delete__ and self.deleted_at is None:
            self.deleted_at = _now()
            if user_id:
                self.updated_by_id = user_id
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()

    def restore(self, user_id: int = None):
        """Undo soft delete."""
        if not self.__soft_delete__:
            return
        self.deleted_at = None
        if user_id:
            self.updated_by_id = user_id
        db.session.commit()

    @classmethod
    def bulk_create(cls, rows: list, user_id: int = None):
        """Insert a list of dicts in one commit. Returns list of created instances."""
        objs = []
        for data in rows:
            obj = cls()
            for col in cls.__table__.columns:
                if col.name not in cls._SKIP and col.name in data:
                    setattr(obj, col.name, data[col.name])
            if user_id:
                obj.created_by_id = user_id
                obj.updated_by_id = user_id
            obj.before_save(is_new=True)
            db.session.add(obj)
            objs.append(obj)
        db.session.commit()
        for obj in objs:
            obj.after_save(is_new=True)
        return objs

    @classmethod
    def bulk_delete(cls, ids: list, user_id: int = None):
        """Delete or soft-delete a list of PKs in one commit."""
        objs = cls.query.filter(cls.id.in_(ids)).all()
        for obj in objs:
            if cls.__soft_delete__ and obj.deleted_at is None:
                obj.deleted_at = _now()
                if user_id:
                    obj.updated_by_id = user_id
            else:
                db.session.delete(obj)
        db.session.commit()

    @classmethod
    def bulk_update(cls, ids: list, data: dict, user_id: int = None):
        """Apply the same field updates to all rows in ids list."""
        objs = cls.query.filter(cls.id.in_(ids)).all()
        skip = cls._SKIP - {"updated_by_id"}
        for obj in objs:
            for col in cls.__table__.columns:
                if col.name not in skip and col.name in data:
                    setattr(obj, col.name, data[col.name])
            if user_id:
                obj.updated_by_id = user_id
        db.session.commit()
        return objs

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self, include: list = None, exclude: list = None) -> dict:
        """
        Serialize to dict.
        include: whitelist of field names (if given, only these are returned)
        exclude: blacklist of field names
        """
        excl = set(exclude or [])
        incl = set(include) if include else None
        result = {}
        for col in self.__table__.columns:
            if incl and col.name not in incl:
                continue
            if col.name in excl:
                continue
            val = getattr(self, col.name, None)
            from decimal import Decimal
            if isinstance(val, datetime): result[col.name] = val.isoformat()
            elif isinstance(val, Decimal): result[col.name] = float(val)
            else: result[col.name] = val
        for out_key, (rel_attr, rel_field) in (self.__serialize_relations__ or {}).items():
            if incl and out_key not in incl:
                continue
            if out_key in excl:
                continue
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None
        return result

    def to_json(self) -> dict:
        return self.to_dict()

    def to_json_str(self) -> str:
        """Return JSON string (useful for caching / logging)."""
        import json
        return json.dumps(self.to_dict(), default=str)

    @classmethod
    def list_to_dict(cls, rows: list, include: list = None, exclude: list = None) -> list:
        """Serialize a list of model instances to a list of dicts."""
        return [r.to_dict(include=include, exclude=exclude) for r in rows]

    def diff(self, data: dict) -> dict:
        """Return {field: (old, new)} for fields in data that differ from current values."""
        changes = {}
        for col in self.__table__.columns:
            if col.name in data:
                old = getattr(self, col.name, None)
                new = data[col.name]
                if old != new:
                    changes[col.name] = (old, new)
        return changes

    # ── Aggregates ────────────────────────────────────────────────────────────

    @classmethod
    def sum(cls, field: str, **filters):
        from sqlalchemy import func
        col = getattr(cls, field)
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return q.with_entities(func.sum(col)).scalar() or 0

    @classmethod
    def avg(cls, field: str, **filters):
        from sqlalchemy import func
        col = getattr(cls, field)
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return q.with_entities(func.avg(col)).scalar()

    @classmethod
    def max_val(cls, field: str, **filters):
        from sqlalchemy import func
        col = getattr(cls, field)
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return q.with_entities(func.max(col)).scalar()

    @classmethod
    def min_val(cls, field: str, **filters):
        from sqlalchemy import func
        col = getattr(cls, field)
        q = cls._q()
        if filters:
            q = q.filter_by(**filters)
        return q.with_entities(func.min(col)).scalar()

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


class ArasSoftModel(ArasModel):
    __abstract__ = True
    __soft_delete__ = True

    deleted_at = db.Column(db.DateTime, nullable=True)
