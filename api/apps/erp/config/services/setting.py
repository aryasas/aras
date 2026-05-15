import json
from typing import Optional
from sqlalchemy.orm import Session
from ..models import Setting


class SettingService:
    @staticmethod
    def get(db: Session, key: str, default=None) -> Optional[str]:
        row = db.query(Setting).filter(Setting.key == key).first()
        return row.value if row else default

    @staticmethod
    def set(db: Session, key: str, value: str, value_type: str = "str") -> Setting:
        row = db.query(Setting).filter(Setting.key == key).first()
        if row:
            row.value = value
            row.value_type = value_type
        else:
            row = Setting(key=key, value=value, value_type=value_type)
            db.add(row)
        db.commit()
        return row

    @staticmethod
    def get_typed(db: Session, key: str, default=None):
        row = db.query(Setting).filter(Setting.key == key).first()
        if not row or row.value is None:
            return default
        try:
            if row.value_type == "int":
                return int(row.value)
            if row.value_type == "float":
                return float(row.value)
            if row.value_type == "bool":
                return row.value.strip().lower() == "true"
            if row.value_type == "json":
                return json.loads(row.value)
            return row.value
        except (ValueError, json.JSONDecodeError):
            return default
