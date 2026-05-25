from typing import Optional
from sqlalchemy import String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from apps.base import MasterDataBase
from core import Aras
from core.response import ok
from core.exceptions import ValidationException

class Report(MasterDataBase):
    __tablename__ = "erp_report_reports"

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="")
    report_type: Mapped[str] = mapped_column(String(20), default="builtin", info={"choices": ["builtin", "orm"]})
    module: Mapped[str] = mapped_column(String(50), default="General")
    columns_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    query_filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, doc="ORM filter config: list of {field, op, value}")
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True, info={"form_hidden": True}, doc="Legacy script/custom SQL storage. Disabled for report execution.")
    linked_doctype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    def before_save(self, is_new: bool, db=None):
        super().before_save(is_new, db=db)
        if self.report_type not in {"builtin", "orm"}:
            raise ValidationException("Only builtin and ORM reports are supported. Raw SQL and Python scripts are disabled.")
        if self.script:
            raise ValidationException("Raw SQL and Python script reports are disabled. Use builtin or ORM report definitions.")

    @Aras.model_action(name="generate_report", permission="read", label="Generate Report", icon="pi pi-play")
    def generate_report(self, db):
        """
        Action to execute the report logic.
        """
        from .services.report_service import ReportService
        report_data = ReportService.generate(self, db=db)
        return ok(report_data, message="Report generated successfully.")
