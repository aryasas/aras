# -*- coding: utf-8 -*-
"""
arasCore/database.py
DB configuration + base mixins (merged from lib/db.py, db_helper.py, db_utils.py)
"""
import os
from flask_login import current_user
from sqlalchemy import MetaData
from sqlalchemy.orm import declarative_base
from arasCore.lib.extensions import db

# Naming convention for Alembic
meta = MetaData(naming_convention={
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
})

ArasBase = declarative_base(metadata=meta)


def configure_database(app):
    """Called from create_app() to finalize DB setup."""
    with app.app_context():
        db.create_all()


# ── Mixins ────────────────────────────────────────────────────────────────────

class TimestampMixin:
    """Adds created_at / updated_at columns."""
    from datetime import datetime
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserStampMixin:
    """Adds created_by / updated_by FK to auth_users."""

    @staticmethod
    def _current_user_id_or_none():
        try:
            return current_user.id if current_user.is_authenticated else None
        except Exception:
            return None

    from sqlalchemy.ext.declarative import declared_attr

    @declared_attr
    def created_by_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey("auth_users.id", name=f"fk_{cls.__name__}_created_by_id", use_alter=True),
            default=cls._current_user_id_or_none,
        )

    @declared_attr
    def updated_by_id(cls):
        return db.Column(
            db.Integer,
            db.ForeignKey("auth_users.id", name=f"fk_{cls.__name__}_updated_by_id", use_alter=True),
            default=cls._current_user_id_or_none,
            onupdate=cls._current_user_id_or_none,
        )


class CRUDMixin:
    """Basic CRUD helpers."""

    def get_all(self):
        return self.query.all()

    def get_by_id(self, id):
        return self.query.filter_by(id=id).first()

    def save(self):
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()


class ArasModel(CRUDMixin, db.Model):
    """Base model — inherit this in all app models."""
    __abstract__ = True
