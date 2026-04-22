"""
arasCore/lib/tx.py — Unified transaction context manager.

Usage:
    from arasCore.lib.tx import tx

    with tx():
        db.session.add(obj)
        # commits on success, rolls back + re-raises on any exception
"""
from contextlib import contextmanager

from arasCore.lib.extensions import db


@contextmanager
def tx():
    """Commit on clean exit, rollback + re-raise on exception."""
    try:
        yield db.session
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
