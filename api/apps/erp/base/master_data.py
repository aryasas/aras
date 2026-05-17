from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MasterDataBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]
    __scoped_by__ = [("org_id", "erp_config_organizations")]

    org_id: Mapped[int] = mapped_column(Integer, ForeignKey("erp_config_organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200))
