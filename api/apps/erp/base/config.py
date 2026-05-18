from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from .erp_base import ErpBase

class ConfigBase(ErpBase):
    __abstract__ = True
    __features__ = ["audit"]
    name: Mapped[str] = mapped_column(String(200))
