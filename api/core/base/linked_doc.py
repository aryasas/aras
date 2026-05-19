"""
LinkedDoc — declarative cross-model relationship descriptor.

Declare __linked_docs__ on any model class. The framework calls
get_linked_documents(db) for the /linked-documents API endpoint and
_cascade_linked_docs(db) automatically during delete_self.

Usage — only table + filters required:

    class InflowInvoice(DocumentBase):
        __linked_docs__ = [
            LinkedDoc(
                table="erp_accounting_entries",
                filters={"source_type": "@class_name", "source_id": "@id"},
                cascade=True,
            ),
            LinkedDoc(
                table="erp_stock_movements",
                filters={"origin_model": "@class_name", "origin_id": "@id"},
                cascade=True,
            ),
        ]

    class JournalEntry(DocumentBase):
        __linked_docs__ = [
            LinkedDoc(
                table="erp_accounting_inflow_invoices",
                filters={"id": "@source_id"},
                condition=lambda self: self.source_type == "InflowInvoice",
                cascade=True,
            ),
        ]

    # cascade-only (no card shown in UI):
    LinkedDoc(table="erp_stock_movement_lines", filters={"movement_id": "@id"}, cascade=True, show=False)

Supported filter value prefixes:
  "@id"         → instance.id
  "@class_name" → instance.__class__.__name__
  "@<attr>"     → getattr(instance, attr)
"""

import re
from dataclasses import dataclass
from typing import Callable, Optional


def _camel_to_words(name: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def _resolve_table(tablename: str):
    """Return (model_cls, resource_url) for a DB tablename using the model + app registry."""
    from .model import Model
    from .app import App

    model_cls = Model._registry.get(tablename)
    if not model_cls:
        raise ValueError(f"LinkedDoc: no model registered for table '{tablename}'")

    resource: Optional[str] = None
    for app_cls in App._registry.values():
        if any(getattr(m, "__tablename__", None) == tablename for m in (app_cls.models or [])):
            resource = app_cls._get_clean_path(tablename).lstrip("/")
            break

    if resource is None:
        resource = tablename.replace("_", "-")

    return model_cls, resource


@dataclass
class LinkedDoc:
    table: str                           # DB tablename — auto-resolves everything
    filters: dict                        # filter kwargs with "@attr" placeholders
    label: str = ""                      # leave blank to auto-derive from class name
    resource: str = ""                   # leave blank to auto-resolve from app registry
    model_factory: Optional[Callable] = None  # leave None to auto-resolve from Model._registry
    display_field: str = "number"
    cascade: bool = False                # soft-delete linked records when parent is deleted
    show: bool = True                    # include in /linked-documents response (cascade-only → False)
    condition: Optional[Callable] = None # (instance) -> bool — skip this entry if False

    def _resolve(self):
        model_cls = self.model_factory() if self.model_factory else None
        resource = self.resource
        label = self.label

        if model_cls is None or not resource or not label:
            _model_cls, _resource = _resolve_table(self.table)
            model_cls = model_cls or _model_cls
            resource = resource or _resource
            label = label or _camel_to_words(model_cls.__name__.replace("Model", "").replace("View", ""))

        return model_cls, resource, label

    def _active(self, instance) -> bool:
        return self.condition is None or self.condition(instance)

    def _resolve_filters(self, instance) -> dict:
        resolved = {}
        for key, val in self.filters.items():
            if isinstance(val, str) and val.startswith("@"):
                attr = val[1:]
                resolved[key] = instance.__class__.__name__ if attr == "class_name" else getattr(instance, attr, None)
            else:
                resolved[key] = val
        return resolved

    def _query(self, db, instance):
        if not self._active(instance):
            return []
        model_cls, _, _ = self._resolve()
        return db.query(model_cls).filter_by(**self._resolve_filters(instance)).all()

    def to_dict_list(self, db, instance) -> list:
        if not self.show:
            return []
        model_cls, resource, label = self._resolve()
        return [
            {
                "label": label,
                "resource": resource,
                "id": obj.id,
                "number": getattr(obj, self.display_field, None) or getattr(obj, "number", None) or getattr(obj, "name", None) or str(obj.id),
            }
            for obj in self._query(db, instance)
        ]

    def delete_linked(self, db, instance):
        for obj in self._query(db, instance):
            if hasattr(obj, "deleted_at") and getattr(obj, "deleted_at") is None:
                obj.delete_self(db)
            else:
                db.delete(obj)
