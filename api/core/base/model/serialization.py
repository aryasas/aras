from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import List, Callable, Any, Optional

class SerializationMixin:
    """Serialization and UI metadata logic for Model."""

    @classmethod
    def get_ui_metadata(cls):
        """Unified access to UI metadata, prioritizing Views and falling back to UIGenerator."""
        from ..view import View
        from ...logic.ui_generator import UIGenerator
        
        view = View.get_for_model(cls)
        if view:
            return view.render_metadata()
        return UIGenerator.generate_metadata(cls)

    def to_dict(self, include: list = None, exclude: list = None) -> dict:
        """Generic serialization into a dictionary, respecting metadata flags."""
        excl = set(exclude or [])
        incl = set(include) if include else None
        result = {}
        for col in self.__table__.columns:
            if incl and col.name not in incl: continue
            if col.name in excl: continue
            if col.info.get("hidden", False) and (not incl or col.name not in incl):
                continue

            val = getattr(self, col.name, None)
            if isinstance(val, (datetime, date)): result[col.name] = val.isoformat()
            elif isinstance(val, Decimal): result[col.name] = float(val)
            elif isinstance(val, Enum): result[col.name] = val.value
            else: result[col.name] = val
            
        serialize_relations = getattr(self, "__serialize_relations__", {})
        for out_key, (rel_attr, rel_field) in (serialize_relations or {}).items():
            if incl and out_key not in incl: continue
            if out_key in excl: continue
            related = getattr(self, rel_attr, None)
            result[out_key] = getattr(related, rel_field, None) if related is not None else None

        # Include Computed Fields
        computed_fields = getattr(self, "_computed", [])
        for name in computed_fields:
            if incl and name not in incl: continue
            if name in excl: continue
            attr = getattr(self, name)
            val = attr() if callable(attr) else attr
            if isinstance(val, (datetime, date)): result[name] = val.isoformat()
            elif isinstance(val, Decimal): result[name] = float(val)
            else: result[name] = val

        return result
