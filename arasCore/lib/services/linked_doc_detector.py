# -*- coding: utf-8 -*-
"""
Detect documents linked to a given model instance, for cascade-delete preview.

Detection passes (in order):
  1. SQLAlchemy ONETOMANY relationships with cascade containing 'delete-orphan'
  2. origin_model / origin_id registry (_ORIGIN_MODEL_REGISTRY)
  3. Explicit __linked_docs__ declarations on the model class

Result is sorted deepest-first — safe deletion order.
"""
from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class LinkedDocNode:
    model_cls:     object          # SA model class
    instance:      object          # SA model instance
    doc_type:      str
    doc_id:        int
    display:       str
    depth:         int
    app_slug:      Optional[str]   = None
    resource_slug: Optional[str]   = None
    admin_url:     Optional[str]   = None

    def as_dict(self) -> dict:
        return {
            "doc_type":     self.doc_type,
            "doc_id":       self.doc_id,
            "display":      self.display,
            "depth":        self.depth,
            "app_slug":     self.app_slug,
            "resource_slug": self.resource_slug,
            "admin_url":    self.admin_url,
        }


def _resolve_url_info(model_cls) -> tuple[Optional[str], Optional[str], str]:
    """Return (app_slug, resource_slug, admin_url_prefix) for a model class."""
    try:
        from arasCore.lib.services.api_handler import get_api_registry
        registry = get_api_registry()
        for key, entry in registry.items():
            if entry.get("model") is model_cls:
                parts = key.split("/", 1)
                app_slug     = parts[0] if len(parts) > 0 else None
                resource_slug = parts[1] if len(parts) > 1 else key
                return app_slug, resource_slug, f"/admin/{key}/"
    except Exception:
        pass
    return None, None, ""


def _get_display(obj) -> str:
    for attr in ("name", "title", "number", "code", "reference"):
        val = getattr(obj, attr, None)
        if val:
            return str(val)
    return f"#{getattr(obj, 'id', '?')}"


def _collect(obj, visited: set, depth: int, results: list) -> None:
    key = (type(obj).__name__, getattr(obj, "id", None))
    if key in visited:
        return
    visited.add(key)

    model_cls = type(obj)
    app_slug, resource_slug, url_prefix = _resolve_url_info(model_cls)
    obj_id = getattr(obj, "id", None)
    admin_url = f"{url_prefix}{obj_id}/" if url_prefix and obj_id else None

    node = LinkedDocNode(
        model_cls=model_cls,
        instance=obj,
        doc_type=model_cls.__name__,
        doc_id=obj_id,
        display=_get_display(obj),
        depth=depth,
        app_slug=app_slug,
        resource_slug=resource_slug,
        admin_url=admin_url,
    )
    results.append(node)

    # Pass 1 — SA cascade ONETOMANY relationships
    try:
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(model_cls)
        for rel in mapper.relationships:
            if rel.direction.name != "ONETOMANY":
                continue
            cascade = str(rel.cascade)
            if "delete-orphan" not in cascade:
                continue
            child_cls = rel.mapper.class_
            # get the FK column name on the child side
            fk_cols = list(rel.remote_side)
            if not fk_cols:
                continue
            fk_attr = fk_cols[0].key
            children = child_cls.query.filter(
                getattr(child_cls, fk_attr) == obj_id
            ).all()
            for child in children:
                _collect(child, visited, depth + 1, results)
    except Exception:
        pass

    # Pass 2 — origin_model / origin_id registry
    try:
        from arasCore.lib.models.deletion_models import _ORIGIN_MODEL_REGISTRY
        tablename = getattr(model_cls, "__tablename__", "")
        for _slug, pointing_cls in _ORIGIN_MODEL_REGISTRY.items():
            if not (hasattr(pointing_cls, "origin_model") and hasattr(pointing_cls, "origin_id")):
                continue
            children = pointing_cls.query.filter_by(
                origin_model=tablename,
                origin_id=obj_id,
            ).all()
            for child in children:
                _collect(child, visited, depth + 1, results)
    except Exception:
        pass

    # Pass 3 — explicit __linked_docs__ on model
    linked_decls = getattr(model_cls, "__linked_docs__", None)
    if linked_decls:
        for decl in linked_decls:
            model_name = decl.get("model_name")
            fk_field   = decl.get("fk_field")
            fk_on_self = decl.get("fk_on_self", False)
            origin_val = decl.get("origin_model_value")
            if not model_name or not fk_field:
                continue
            try:
                from sqlalchemy import inspect as sa_inspect
                target_cls = None
                for m in sa_inspect(model_cls).mapper.registry.mappers:
                    if m.class_.__name__ == model_name:
                        target_cls = m.class_
                        break
                if target_cls is None:
                    continue

                if fk_on_self:
                    fk_val = getattr(obj, fk_field, None)
                    if fk_val:
                        target = target_cls.query.get(fk_val)
                        if target:
                            _collect(target, visited, depth + 1, results)
                elif origin_val:
                    children = target_cls.query.filter_by(
                        origin_model=origin_val,
                        **{fk_field: obj_id},
                    ).all()
                    for child in children:
                        _collect(child, visited, depth + 1, results)
                else:
                    children = target_cls.query.filter(
                        getattr(target_cls, fk_field) == obj_id
                    ).all()
                    for child in children:
                        _collect(child, visited, depth + 1, results)
            except Exception:
                pass


def detect_linked_docs(obj) -> list:
    """
    Return a flat list of LinkedDocNode for all documents transitively linked
    to `obj`, sorted deepest-first (safe deletion order).
    The root `obj` itself is NOT included.
    """
    results: list = []
    visited: set  = set()

    # seed visited with root so it isn't added to results
    root_key = (type(obj).__name__, getattr(obj, "id", None))
    visited.add(root_key)

    model_cls = type(obj)
    obj_id    = getattr(obj, "id", None)
    tablename = getattr(model_cls, "__tablename__", "")

    # Pass 1 — SA cascade ONETOMANY
    try:
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(model_cls)
        for rel in mapper.relationships:
            if rel.direction.name != "ONETOMANY":
                continue
            if "delete-orphan" not in str(rel.cascade):
                continue
            child_cls = rel.mapper.class_
            fk_cols = list(rel.remote_side)
            if not fk_cols:
                continue
            fk_attr = fk_cols[0].key
            children = child_cls.query.filter(
                getattr(child_cls, fk_attr) == obj_id
            ).all()
            for child in children:
                _collect(child, visited, 1, results)
    except Exception:
        pass

    # Pass 2 — origin_model registry
    try:
        from arasCore.lib.models.deletion_models import _ORIGIN_MODEL_REGISTRY
        for _slug, pointing_cls in _ORIGIN_MODEL_REGISTRY.items():
            if not (hasattr(pointing_cls, "origin_model") and hasattr(pointing_cls, "origin_id")):
                continue
            children = pointing_cls.query.filter_by(
                origin_model=tablename,
                origin_id=obj_id,
            ).all()
            for child in children:
                _collect(child, visited, 1, results)
    except Exception:
        pass

    # Pass 3 — __linked_docs__
    linked_decls = getattr(model_cls, "__linked_docs__", None)
    if linked_decls:
        for decl in linked_decls:
            model_name  = decl.get("model_name")
            fk_field    = decl.get("fk_field")
            fk_on_self  = decl.get("fk_on_self", False)  # FK is on THIS model pointing to target
            origin_val  = decl.get("origin_model_value")
            if not model_name or not fk_field:
                continue
            try:
                from sqlalchemy import inspect as sa_inspect
                target_cls = None
                for m in sa_inspect(model_cls).mapper.registry.mappers:
                    if m.class_.__name__ == model_name:
                        target_cls = m.class_
                        break
                if target_cls is None:
                    continue

                if fk_on_self:
                    # FK is on the current obj (e.g. obj.journal_entry_id → AccJournalEntry)
                    fk_val = getattr(obj, fk_field, None)
                    if fk_val:
                        target = target_cls.query.get(fk_val)
                        if target:
                            _collect(target, visited, 1, results)
                elif origin_val:
                    children = target_cls.query.filter_by(
                        origin_model=origin_val,
                        **{fk_field: obj_id},
                    ).all()
                    for child in children:
                        _collect(child, visited, 1, results)
                else:
                    children = target_cls.query.filter(
                        getattr(target_cls, fk_field) == obj_id
                    ).all()
                    for child in children:
                        _collect(child, visited, 1, results)
            except Exception:
                pass

    # Sort deepest-first
    results.sort(key=lambda n: (-n.depth, n.doc_id or 0))
    return results
