# -*- coding: utf-8 -*-
"""
arasCore/aras_gen/db.py
=======================
ArasDB — single import handle to the Flask-SQLAlchemy instance and
common helpers. ``ArasGen.DB`` aliases ``arasCore.lib.core.extensions.db``.
"""
from __future__ import annotations
from arasCore.lib.core.extensions import db as _db


class ArasDB:
    """Namespace for DB primitives. Use ``ArasGen.DB.session`` etc."""
    db      = _db
    session = _db.session
    Column  = _db.Column
    relationship = _db.relationship
    ForeignKey   = _db.ForeignKey


__all__ = ["ArasDB"]
