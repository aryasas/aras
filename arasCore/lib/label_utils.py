_AUTO_CANDIDATES = ("name", "title", "code", "username", "label")
_SEP = " — "

# Cache: db_table_name → list[str] of display field names
_display_cache: dict = {}


def humanize(name: str) -> str:
    """'fiscal_period_id' → 'Fiscal Period',  'date_entry' → 'Date Entry'"""
    n = name[:-3] if name.endswith("_id") else name
    return n.replace("_", " ").title()


def invalidate_display_cache(tablename: str = None):
    if tablename:
        _display_cache.pop(tablename, None)
    else:
        _display_cache.clear()


def _get_display_fields(tablename: str) -> list:
    """Return the configured or auto-detected display field names for a table."""
    if tablename in _display_cache:
        return _display_cache[tablename]
    fields = []
    try:
        from arasCore.arasAdmin.models import AppManagerTable
        tbl = AppManagerTable.query.filter_by(db_table_name=tablename).first()
        if tbl and tbl.display_columns:
            fields = [f.strip() for f in tbl.display_columns.split(",") if f.strip()]
    except Exception:
        pass
    _display_cache[tablename] = fields
    return fields


def find_ref_model(ref_tname: str):
    """
    Return the canonical (non-dynamic) SQLAlchemy model class for a DB table name.
    Prefers code-defined models over DynModel_* service models when duplicates exist.
    """
    try:
        from arasCore.lib.extensions import db
        candidates = [
            m.class_ for m in db.Model.registry.mappers
            if m.local_table.name == ref_tname
        ]
        for cls in candidates:
            if not cls.__name__.startswith("DynModel_"):
                return cls
        return candidates[0] if candidates else None
    except Exception:
        return None


def row_display(row) -> str:
    """
    Return the human-readable display string for a related row.
    Resolution order:
      1. AppManagerTable.display_columns  (DB setting, user-configurable)
      2. Model.__display_fields__          (tuple declared on model class)
      3. Auto-detect                       (first of name/title/code/username)
    Always returns a string — never a raw ID integer.
    """
    tname = getattr(row.__class__, "__tablename__", None)

    # 1. DB setting
    fields = _get_display_fields(tname) if tname else []
    if fields:
        parts = [str(getattr(row, f, "") or "") for f in fields]
        result = _SEP.join(p for p in parts if p)
        if result:
            return result

    # 2. Model class declaration
    class_fields = getattr(row.__class__, "__display_fields__", None)
    if class_fields:
        parts = [str(getattr(row, f, "") or "") for f in class_fields]
        result = _SEP.join(p for p in parts if p)
        if result:
            return result

    # 3. Auto-detect
    for candidate in _AUTO_CANDIDATES:
        val = getattr(row, candidate, None)
        if val:
            return str(val)

    return str(row.id)
