from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from core import Aras

class MasterDataBase(Aras.Model):
    __abstract__ = True
    __features__ = ["audit", "scoped"]
    __scoped_by__ = [("company_id", "erp_config_companies")]
    code: Mapped[str] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(200))
