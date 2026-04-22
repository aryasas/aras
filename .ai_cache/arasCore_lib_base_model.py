from datetime import datetime, timezone
from arasCore.lib.extensions import db


def _now():
    return datetime.now(timezone.utc)


class ArasModel(db.Model):
    __abstract__ = True
    __soft_delete__: bool = False
    __serialize_relations__: dict = {}

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    is_active     = db.Column(db.Boolean, default=True, nullable=False)
    created_at    = db.Column(db.DateTime, default=_now, nullable=False)
    updated_at    = db.Column(db.DateTime, default=_now, onupdate=_now, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=True)

    # Only physically present when __soft_delete__ = True; declared None so it's always referenceable
    deleted_at = None

    # ── Hooks ─────────────────────────────────────────────────────────────────

    def before_save(self, is_new: bool): pass
    def after_save(self, is_new: bool): pass

    # ── Queries ───────────────────────────────────────────────────────────────

    @classmethod
    def get(cls, item_id: int):
        return cls.query.get(item_id)

    @classmethod
    def get_or_404(cls, item_id: int):
        from flask import abort
        obj = cls.query.get(item_id)
        if obj is None:
            abort(404)
        return obj

    @classmethod
    def list_all(cls, active_only: bool = False):
        q = cls.query
        if active_only:
            q = q.filter_by(is_active=True)
        if cls.__soft_delete__:
            q = q.filter(cls.deleted_at.is_(None))
        return q.order_by(cls.id.desc()).all()

    # ── Write ─────────────────────────────────────────────────────────────────

    _SKIP = frozenset({"id", "created_at", "updated_at", "created_by_id", "updated_by_id", "deleted_at"})

    @classmethod
    def create(cls, data: dict, user_id: int = None):
        obj = cls()
        for col in cls.__table__.columns:
            if col.name not in cls._SKIP and col.name in data:
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
        skip = self._SKIP - {"updated_by_id"}
        for col in self.__table__.columns:
            if col.name not in skip and col.name in data:
                setattr(self, col.name, data[col.name])
        if user_id:
            self.updated_by_id = user_id
        self.before_save(is_new=False)
        db.session.commit()
        self.after_save(is_new=False)
        return self

    def delete_self(self, user_id: int = None):
        if self.__soft_delete__ and self.deleted_at is not None:
            self.deleted_at = _now()
            if user_id:
                self.updated_by_id = user_id
            db.session.commit()
        else:
            db.session.delete(self)
            db.session.commit()

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        result = {}
        for col in self.__table__.columns:
            val = getattr(self, col.name)
            result[col.name] = val.isoformat() if isinstance(val, datetime) else val
        for out_key, (rel_attr, rel_field) in (self.__serialize_relations__ or {}).items():
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__} id={getattr(self, 'id', '?')}>"


class ArasSoftModel(ArasModel):
    """Convenience subclass with soft delete pre-enabled."""
    __abstract__ = True
    __soft_delete__ = True

    deleted_at = db.Column(db.DateTime, nullable=True)
