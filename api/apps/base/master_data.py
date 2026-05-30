from sqlalchemy import String, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from .erp_base import ErpBase

class MasterDataBase(ErpBase):
    __abstract__ = True
    __soft_delete__ = True
    __features__ = ["audit"]
    __scoped_by__ = [("org_id", "config_organizations")]

    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("config_organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200))
    is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
