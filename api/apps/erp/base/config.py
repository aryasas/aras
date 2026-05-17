from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class ConfigBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]
    name: Mapped[str] = mapped_column(String(200))
