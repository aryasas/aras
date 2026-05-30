from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .master_data import MasterDataBase

class SavedFilter(MasterDataBase):
    __tablename__ = "base_saved_filters"
    resource: Mapped[str] = mapped_column(String(100))   # e.g. "accounting_accounts"
    name: Mapped[str] = mapped_column(String(100))
    filters_json: Mapped[str] = mapped_column(Text)       # JSON blob of filter state
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
