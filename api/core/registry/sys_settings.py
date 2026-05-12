from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped
from ..base.model import Model
from ..base.field import Field
import core

class ArasSetting(Model):
    __tablename__ = "sys_settings"
    __title__ = "System Settings"

    key: Mapped[str] = Field(String(100), unique=True, label="Setting Key", searchable=True)
    value: Mapped[str] = Field(Text, label="Value", ui_type="textarea")
    description: Mapped[str] = Field(String(255), nullable=True, label="Description")

    @classmethod
    def get(cls, key: str, default: str = None):
        """Fetch a setting value by key."""
        db = core.Aras.db()
        try:
            row = db.query(cls).filter(cls.key == key).first()
            return row.value if row else default
        finally:
            db.close()

    @classmethod
    def set(cls, key: str, value: str, description: str = None):
        """Set a setting value by key."""
        db = core.Aras.db()
        try:
            row = db.query(cls).filter(cls.key == key).first()
            if row:
                row.value = str(value)
                if description:
                    row.description = description
            else:
                row = cls(key=key, value=str(value), description=description)
                db.add(row)
            db.commit()
            return row
        finally:
            db.close()
