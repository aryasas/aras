from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from ..base import ConfigBase, MasterDataBase

class Company(MasterDataBase):
    __tablename__ = "erp_config_companies"
    __scoped_by__ = [] 

class Currency(ConfigBase):
    __tablename__ = "erp_config_currencies"
    symbol: Mapped[str] = mapped_column(String(10))

class Uom(ConfigBase):
    __tablename__ = "erp_config_uoms"

class PriceType(ConfigBase):
    __tablename__ = "erp_config_price_types"
    kind: Mapped[str] = mapped_column(String(20), default="sales") # sales or purchase
