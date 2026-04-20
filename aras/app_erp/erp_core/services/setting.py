"""core.setting — typed key/value config store."""
import json
from decimal import Decimal
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.setting import CoreSetting

_cache: dict = {}


def get(key: str, company_id: int = None, user_id: int = None, default=None):
    """Fetch a setting value, cast to declared type. Checks user > company > global."""
    for scope, scope_id in [("user", user_id), ("company", company_id), ("global", None)]:
        if scope != "global" and scope_id is None:
            continue
        cache_key = f"{scope}:{scope_id}:{key}"
        if cache_key in _cache:
            return _cache[cache_key]
        row = CoreSetting.query.filter_by(scope=scope, scope_id=scope_id, key=key).first()
        if row:
            val = _cast(row.value, row.value_type)
            _cache[cache_key] = val
            return val
    return default


def set_value(key: str, value, scope="global", scope_id=None,
              value_type="string", description=None):
    row = CoreSetting.query.filter_by(scope=scope, scope_id=scope_id, key=key).first()
    str_val = json.dumps(value) if value_type == "json" else str(value)
    if row:
        row.value = str_val
    else:
        row = CoreSetting(scope=scope, scope_id=scope_id, key=key,
                          value_type=value_type, value=str_val, description=description)
        db.session.add(row)
    _cache.pop(f"{scope}:{scope_id}:{key}", None)
    db.session.commit()


def clear_cache():
    _cache.clear()


def _cast(value, value_type):
    if value is None:
        return None
    if value_type == "int":
        return int(value)
    if value_type == "decimal":
        return Decimal(value)
    if value_type == "bool":
        return value.lower() in ("1", "true", "yes")
    if value_type == "json":
        return json.loads(value)
    return value
