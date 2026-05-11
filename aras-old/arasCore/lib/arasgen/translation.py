# -*- coding: utf-8 -*-
"""System-wide translation layer.

Stores translations in the ``aras_translation`` table. Every label/menu/column
the framework renders flows through ``_t()`` which:

  1. Reads the active locale (Flask session, or fallback to "en").
  2. Looks up (locale, context_type, context_key, source) in the DB.
  3. Returns the target if found, otherwise the source unchanged.

Context types:
    "label"  — column label (context_key = f"{table}.{column}")
    "table"  — table title  (context_key = table_name)
    "menu"   — menu/group name (context_key = menu_slug)
    "string" — generic UI string (context_key = source itself)

User-editable from GUI: every untranslated string seen in a request is
auto-seeded into the table for translators to fill in.
"""
from __future__ import annotations

import logging
from typing import Optional

from arasCore.lib.core.base_model import ArasModel
from arasCore.lib.core.extensions import db

logger = logging.getLogger(__name__)


class Translation(ArasModel):
    __tablename__ = "aras_translation"
    __table_args__ = (
        db.UniqueConstraint("locale", "context_type", "context_key",
                            name="uq_translation_lookup"),
    )

    locale       = db.Column(db.String(10),  nullable=False, index=True)
    context_type = db.Column(db.String(20),  nullable=False)   # label/table/menu/string
    context_key  = db.Column(db.String(255), nullable=False)
    source       = db.Column(db.Text,        nullable=False)
    target       = db.Column(db.Text,        nullable=True)
    notes        = db.Column(db.Text,        nullable=True)


def get_locale() -> str:
    """Return active locale. Order: g._locale → session.locale → app config → 'en'."""
    try:
        from flask import g, session, current_app, has_app_context, has_request_context
        if has_app_context():
            loc = getattr(g, "_locale", None)
            if loc:
                return loc
            if has_request_context():
                loc = session.get("locale")
                if loc:
                    return loc
            return current_app.config.get("ARAS_LOCALE", "en")
    except Exception:
        pass
    return "en"


def _t(source: str, *, context_type: str = "string", context_key: str | None = None,
       locale: str | None = None) -> str:
    """Translate a string. Falls back to source on miss."""
    if not source:
        return source
    loc = locale or get_locale()
    if loc == "en" or loc.startswith("en"):
        return source  # source is English by convention
    key = context_key or source

    try:
        row = (
            db.session.query(Translation.target)
            .filter_by(locale=loc, context_type=context_type, context_key=key)
            .first()
        )
        if row and row[0]:
            return row[0]
        # Auto-seed for translators
        _seed_translation(loc, context_type, key, source)
    except Exception as e:                              # pragma: no cover
        logger.debug(f"[_t] lookup failed: {e}")
    return source


def _seed_translation(locale: str, ctype: str, key: str, source: str) -> None:
    try:
        exists = (
            db.session.query(Translation.id)
            .filter_by(locale=locale, context_type=ctype, context_key=key)
            .first()
        )
        if exists:
            return
        db.session.add(Translation(
            locale=locale, context_type=ctype, context_key=key, source=source,
        ))
        db.session.commit()
    except Exception:
        try:
            db.session.rollback()
        except Exception:
            pass
