# -*- coding: utf-8 -*-
"""arasgen.model — ArasModel + mixins.

Re-export shim during transition. Mixin split (audit/naming/fetch/...) lives
in sibling files; ArasModel composes them.
"""
from arasCore.arasgen import ArasModel, register, models_for

__all__ = ["ArasModel", "register", "models_for"]
