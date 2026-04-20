# -*- coding: utf-8 -*-
"""
arasCore/lib/base_model.py
==========================
Standard base model untuk semua app-level models.

Setiap model di app_* harus mewarisi ArasModel (bukan db.Model langsung):

    from arasCore.lib.base_model import ArasModel

    class MyModel(ArasModel):
        __tablename__ = "app_my_model"
        name = db.Column(db.String(100), nullable=False)

ArasModel menyediakan:
  - id, created_at, updated_at, created_by_id, updated_by_id  (auto-set)
  - is_active (soft enable/disable)
  - deleted_at (soft delete opsional — aktif jika model set __soft_delete__ = True)
  - CRUD classmethods: get(), list_all(), create(), update_self(), delete_self()
  - to_dict() — default serializer untuk API
  - before_save() / after_save() hooks yang bisa dioverride per model
"""
from datetime import datetime
from arasCore.lib.extensions import db


class ArasModel(db.Model):
    """
    Abstract base untuk semua app-level models.
    Tidak punya __tablename__ — subclass wajib mendefinisikannya.
    """
    __abstract__ = True

    # ── Standard fields ───────────────────────────────────────────────────────
    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_active  = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    # Set __soft_delete__ = True on a subclass to enable soft delete
    __soft_delete__: bool = False

    @classmethod
    def _soft_delete_enabled(cls) -> bool:
        return bool(getattr(cls, "__soft_delete__", False))

    # deleted_at is only physically present when __soft_delete__ is True.
    # We declare it here as None so code can always reference it safely;
    # subclasses that want it should re-declare the column.
    deleted_at = None

    # ── Hooks (override in subclass) ──────────────────────────────────────────

    def before_save(self, is_new: bool):
        """Called before INSERT (is_new=True) or UPDATE (is_new=False). Raise to cancel."""
        pass

    def after_save(self, is_new: bool):
        """Called after successful commit."""
        pass

    # ── CRUD classmethods ─────────────────────────────────────────────────────

    @classmethod
    def get(cls, item_id: int):
        """Return one record or None."""
        return cls.query.get(item_id)

    @classmethod
    def get_or_404(cls, item_id: int):
        """Return one record or raise 404."""
        from flask import abort
        obj = cls.query.get(item_id)
        if obj is None:
            abort(404)
        return obj

    @classmethod
    def list_all(cls, active_only: bool = False):
        """Return all records. Pass active_only=True to filter is_active=True."""
        q = cls.query
        if active_only:
            q = q.filter_by(is_active=True)
        if cls._soft_delete_enabled():
            q = q.filter(cls.deleted_at.is_(None))
        return q.order_by(cls.id.desc()).all()

    @classmethod
    def create(cls, data: dict, user_id: int = None):
        """
        Create and commit a new record from a dict.
        Sets created_by_id / updated_by_id from user_id.
        Returns the new instance.
        """
        obj = cls()
        _SKIP = {"id", "created_at", "updated_at", "created_by_id", "updated_by_id", "deleted_at"}
        for col in cls.__table__.columns:
            if col.name in _SKIP:
                continue
            if col.name in data:
                setattr(obj, col.name, data[col.name])
        if user_id:
            obj.created_by_id = user_id
            obj.updated_by_id = user_id
        obj.before_save(is_new=True)
        db.session.add(obj)
        db.session.commit()
        obj.after_save(is_new=True)
        return obj

    def update_self(self, data: dict, user_id: int = None):
        """
        Update this instance from a dict and commit.
        Returns self.
        """
        _SKIP = {"id", "created_at", "updated_at", "created_by_id", "deleted_at"}
        for col in self.__table__.columns:
            if col.name in _SKIP:
                continue
            if col.name in data:
                setattr(self, col.name, data[col.name])
        if user_id:
            self.updated_by_id = user_id
        self.before_save(is_new=False)
        db.session.commit()
        self.after_save(is_new=False)
        return self

    def delete_self(self, user_id: int = None):
        """
        Delete this record.
        If __soft_delete__ is True, sets deleted_at instead of physical delete.
        """
        if self._soft_delete_enabled() and hasattr(self, "deleted_at"):
            self.deleted_at = datetime.utcnow()
            if user_id:
                self.updated_by_id = user_id
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()

    # ── Serialization ─────────────────────────────────────────────────────────

    # Declare relation fields to inline in to_dict().
    # Format: {"output_key": ("relation_attr", "field_on_related")}
    # Example: {"author_username": ("author", "username")}
    __serialize_relations__: dict = {}

    def to_dict(self) -> dict:
        """
        Default serializer — all column values + declared relation fields.
        Override in subclass for fully custom output.
        """
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            if isinstance(val, datetime):
                val = val.isoformat()
            result[col.name] = val
        for out_key, (rel_attr, rel_field) in (self.__class__.__serialize_relations__ or {}).items():
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None
        return result

    def __repr__(self):
        pk = getattr(self, "id", "?")
        return f"<{self.__class__.__name__} id={pk}>"


class ArasSoftModel(ArasModel):
    """
    Convenience subclass with soft delete enabled and deleted_at column declared.
    Use this for models where records should never be physically deleted.

        class MyLog(ArasSoftModel):
            __tablename__ = "app_my_log"
            ...
    """
    __abstract__ = True
    __soft_delete__ = True

    deleted_at = db.Column(db.DateTime, nullable=True)
