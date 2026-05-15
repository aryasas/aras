from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MasterDataBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit"]
    __scoped_by__ = [("company_id", "erp_config_companies")]

    company_id: Mapped[int] = mapped_column(Integer, ForeignKey("erp_config_companies.id"), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
