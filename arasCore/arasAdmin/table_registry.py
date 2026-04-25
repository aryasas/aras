# -*- coding: utf-8 -*-
"""Table registry — dynamic model/form builders, view columns, cache."""
import logging

from arasCore.lib.extensions import db
from arasCore.lib.label_utils import humanize as _humanize_label

logger = logging.getLogger(__name__)

_SYSTEM_COLS = {"id", "created_at", "updated_at", "deleted_at",
                "created_by", "updated_by", "created_by_id", "updated_by_id"}

# In-process cache:  key = db_table_name  ->  (DynamicModel, DynamicForm, view_columns)
_table_registry: dict = {}


def apply_search_and_filters(query, model, search_cols, request):
    """
    Apply search (q=) and multi-row filters (f_col[], f_op[], f_val[]) to a query.

    search_cols: list of column names to search against (from mgr_column.searchable or caller).
    Returns: (query, active_filters_list, search_q)
    """
    import sqlalchemy as _sa

    active_filters = []

    q = request.args.get("q", "").strip()
    if q and search_cols:
        from sqlalchemy import or_
        clauses = []
        for col_name in search_cols:
            col = getattr(model, col_name, None)
            if col is not None:
                try:
                    clauses.append(col.ilike(f"%{q}%"))
                except Exception:
                    pass
        if clauses:
            query = query.filter(or_(*clauses))

    cols  = request.args.getlist("f_col[]")
    ops   = request.args.getlist("f_op[]")
    vals  = request.args.getlist("f_val[]")

    for col_name, op, val in zip(cols, ops, vals):
        col_name = col_name.strip()
        op       = op.strip()
        val      = val.strip()
        if not col_name or not op:
            continue
        col_attr = getattr(model, col_name, None)
        if col_attr is None:
            continue
        try:
            if op == "equals":
                query = query.filter(col_attr == val)
            elif op == "not_equals":
                query = query.filter(col_attr != val)
            elif op == "like":
                query = query.filter(col_attr.ilike(f"%{val}%"))
            elif op == "not_like":
                query = query.filter(col_attr.notilike(f"%{val}%"))
            elif op == "in":
                items = [v.strip() for v in val.split(",") if v.strip()]
                query = query.filter(col_attr.in_(items))
            elif op == "not_in":
                items = [v.strip() for v in val.split(",") if v.strip()]
                query = query.filter(col_attr.notin_(items))
            elif op == "is":
                query = query.filter(col_attr.is_(None))
                val = ""
            active_filters.append({"col": col_name, "op": op, "val": val})
        except Exception:
            pass

    return query, active_filters, q


def sync_table_columns(model):
    """ALTER TABLE to add any SA model columns missing from the physical DB table."""
    tname = model.__tablename__
    try:
        existing = {row[0] for row in db.session.execute(db.text(f"DESCRIBE `{tname}`")).fetchall()}
    except Exception:
        return
    for col in model.__table__.columns:
        if col.name in existing:
            continue
        try:
            col_def = col.type.compile(dialect=db.engine.dialect)
            nullable = "" if col.nullable is False else " NULL"
            db.session.execute(db.text(f"ALTER TABLE `{tname}` ADD COLUMN `{col.name}` {col_def}{nullable}"))
            db.session.commit()
            logger.info(f"[table_registry] ALTER TABLE {tname} ADD COLUMN {col.name}")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"[table_registry] Could not add column {col.name} to {tname}: {e}")


def clear_cache(app_name=None):
    """Clear cached models/forms, sidebar menu, and SA mapper entries."""
    try:
        from arasCore.lib.audit import invalidate_cache as _audit_invalidate
        _audit_invalidate()
    except Exception:
        pass
    try:
        from arasCore.lib.extensions import cache as _cache
        _cache.delete("_sidebar_raw")
    except Exception:
        pass
    if app_name:
        safe = app_name.replace("-", "_")
        keys = [k for k in _table_registry if k.startswith(f"{safe}_") or k == safe]
    else:
        keys = list(_table_registry.keys())

    for k in keys:
        class_name = f"DynModel_{k}"
        try:
            reg = db.Model.registry._class_registry
            reg.pop(class_name, None)
        except Exception:
            pass
        try:
            if k in db.metadata.tables:
                db.metadata.remove(db.metadata.tables[k])
        except Exception:
            pass
        _table_registry.pop(k, None)


def make_table_model(tbl, app_name, all_tables_in_app=None):
    """
    Build a SQLAlchemy Model for one AppManagerTable.
    all_tables_in_app: list of AppManagerTable in same app, used to resolve FK targets.
    """
    from arasCore.arasAdmin.column_factory import _make_sa_column
    from arasCore.lib.base_model import ArasModel

    db_tname   = tbl.get_db_table_name(app_name)
    class_name = f"DynModel_{db_tname}"

    if db_tname in _table_registry:
        return _table_registry[db_tname][0]

    try:
        existing = db.Model.registry._class_registry.get(class_name)
    except Exception:
        existing = None
    if existing is not None:
        _table_registry.setdefault(db_tname, (existing, None, []))
        return existing

    attrs = {
        "__tablename__":   db_tname,
        "__table_args__":  {"extend_existing": True},
        "id":              db.Column(db.Integer, primary_key=True),
    }

    columns = tbl.get_columns()
    tbl_map = {t.id: t for t in (all_tables_in_app or [])}

    for col in columns:
        if col.field_type == "relation" and col.relation_table_id and col.relation_table_id in tbl_map:
            target_tbl  = tbl_map[col.relation_table_id]
            target_name = target_tbl.get_db_table_name(app_name)
            fk_col_name = f"{col.name}_id"
            attrs[fk_col_name] = db.Column(
                db.Integer, db.ForeignKey(f"{target_name}.id"),
                nullable=not col.required
            )
            rel_class_name = f"DynModel_{target_name}"
            attrs[col.name] = db.relationship(
                rel_class_name, foreign_keys=f"[{class_name}.{fk_col_name}]",
                lazy="select",
            )
        else:
            sa_col = _make_sa_column(col)
            if sa_col is not None:
                attrs[col.name] = sa_col

    def __repr__(self):
        return f"<{tbl.name} id={self.id}>"

    attrs["__repr__"] = __repr__

    DynModel = type(class_name, (ArasModel,), attrs)
    _table_registry[db_tname] = (DynModel, None, [])
    logger.info(f"[table_registry] Model created: {class_name}")
    return DynModel


def make_table_form(tbl, model_cls, app_id):
    """Build a WTForms Form for one AppManagerTable."""
    db_tname = model_cls.__tablename__ if model_cls is not None else str(tbl.id)

    cached = _table_registry.get(db_tname)
    if cached and cached[1] is not None:
        return cached[1]

    from arasCore.lib.forms import build_form_from_table
    DynForm = build_form_from_table(tbl)

    if db_tname in _table_registry:
        m, _, v = _table_registry[db_tname]
        _table_registry[db_tname] = (m, DynForm, v)

    logger.info(f"[table_registry] Form created: {DynForm.__name__}")
    return DynForm


def get_view_columns(tbl):
    """[('Label', 'col_name'), ...] — respects list_columns order and show_in_list flag."""
    all_cols = tbl.get_columns()

    def _col_label(col):
        lbl = col.label or ""
        return lbl if lbl and lbl != col.name else _humanize_label(col.name)

    col_map = {}
    for col in all_cols:
        if col.name in _SYSTEM_COLS:
            continue
        key = f"{col.name}_id" if (col.field_type == "relation" and col.relation_table_id) else col.name
        col_map[col.name] = (_col_label(col), key, col)

    if tbl.list_columns:
        names = [n.strip() for n in tbl.list_columns.split(",") if n.strip()]
        vcols = []
        for name in names:
            if name in col_map:
                label, field_key, _ = col_map[name]
                vcols.append((label, field_key))
        return vcols

    visible = [c for c in all_cols if c.show_in_list and c.name not in _SYSTEM_COLS]
    if not visible:
        visible = [c for c in all_cols if c.name not in _SYSTEM_COLS]
    vcols = []
    for col in visible:
        lbl = _col_label(col)
        if col.field_type == "relation" and col.relation_table_id:
            vcols.append((lbl, f"{col.name}_id"))
        else:
            vcols.append((lbl, col.name))
    return vcols
