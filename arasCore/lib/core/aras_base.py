# -*- coding: utf-8 -*-
"""
ArasBase — single abstract ancestor for all framework components.

Pure Python mixin (no metaclass) so it composes cleanly with
SQLAlchemy's DeclarativeMeta (ArasModel) and WTForms' DefaultMeta (ArasForm).

Auto-registers every subclass into _REGISTRY via __init_subclass__.
"""
from __future__ import annotations
from typing import ClassVar, Type


_REGISTRY: dict[str, Type["ArasBase"]] = {}


class ArasBase:
    """
    Framework root mixin. Inherit in every model, form, handler, service.
    Provides auto-registration and cooperative hook stubs.
    """

    # Optional tag; if blank, __qualname__ is used as registry key.
    _aras_type: ClassVar[str] = ""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        key = getattr(cls, "_aras_type", "") or cls.__qualname__
        _REGISTRY[key] = cls
        cls.on_register()

    # ------------------------------------------------------------------ hooks

    @classmethod
    def on_register(cls):
        """Fired once at class-definition time. Override + call super()."""

    @classmethod
    def on_load(cls):
        """Fired by the framework when the owning app is activated."""

    # ------------------------------------------------------------------ utils

    @classmethod
    def framework_subclasses(cls) -> list[Type["ArasBase"]]:
        """All registered descendants of this specific class."""
        return [v for v in _REGISTRY.values() if issubclass(v, cls) and v is not cls]

    @classmethod
    def registry(cls) -> dict[str, Type["ArasBase"]]:
        return _REGISTRY


def get_registry() -> dict[str, Type["ArasBase"]]:
    return _REGISTRY
