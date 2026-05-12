from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped
from core import Aras

class ArasSetting(Aras.Model):
    __tablename__ = "sys_settings"
    __title__ = "System Settings"

    key: Mapped[str] = Aras.Column(String(100), unique=True, label="Setting Key", searchable=True)
    value: Mapped[str] = Aras.Column(Text, label="Value", ui_type="textarea")
    description: Mapped[str] = Aras.Column(String(255), nullable=True, label="Description")
