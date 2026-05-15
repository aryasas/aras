from typing import Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base import MasterDataBase
from core import Aras

class Report(MasterDataBase):
    __tablename__ = "erp_report_reports"
    
    report_type: Mapped[str] = mapped_column(String(20), default="query", info={"choices": ["query", "script", "jinja"]})
    module: Mapped[str] = mapped_column(String(50), default="General")
    columns_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    linked_doctype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    @Aras.model_action(name="generate_report", permission="read", label="Generate Report", icon="pi pi-play")
    def generate_report(self):
        """
        Action to execute the report logic.
        """
        from .services.report_service import ReportService
        return ReportService.generate(self)
