from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped
from core import Aras

class ArasSetting(Aras.Model):
    __tablename__ = "sys_settings"
    __title__ = "System Settings"

    key: Mapped[str] = Aras.Column(String(100), unique=True, label="Setting Key", searchable=True)
    value: Mapped[str] = Aras.Column(Text, label="Value", ui_type="textarea")
    description: Mapped[str] = Aras.Column(String(255), nullable=True, label="Description")

    @classmethod
    def get(cls, key: str, default: str = None):
        """Fetch a setting value by key."""
        db = Aras.db()
        try:
            row = db.query(cls).filter(cls.key == key).first()
            return row.value if row else default
        finally:
            db.close()

    @classmethod
    def set(cls, key: str, value: str, description: str = None):
        """Set a setting value by key."""
        db = Aras.db()
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
