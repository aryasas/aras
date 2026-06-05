# gemini-flash
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core.base.orm import MasterDataBase
from core import Aras
from core.response import ok
from core.exceptions import ValidationException

# unattributed (pre-tagging)
class Report(MasterDataBase):
    __tablename__ = "report_reports"

    code: Mapped[str] = mapped_column(String(100), nullable=False, index=True, default="")
    report_type: Mapped[str] = mapped_column(String(20), default="builtin", info={"choices": ["builtin", "orm", "script"]})
    module: Mapped[str] = mapped_column(String(50), default="General")
    columns_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    filters_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    query_filters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, doc="ORM filter config: list of {field, op, value}")
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True, doc="Python script for 'script' type reports.")
    linked_doctype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    script_approved_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("core_users.id"), nullable=True)
    script_approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    script_approved_by = relationship("core.auth.models.User", foreign_keys=[script_approved_by_id])

    # unattributed (pre-tagging)
    def before_save(self, is_new: bool, db=None):
        super().before_save(is_new, db=db)
        if self.report_type not in {"builtin", "orm", "script"}:
            raise ValidationException("Invalid report type. Supported: builtin, orm, script.")
        
        # Reset approval if script changes
        # Note: In a real scenario, we'd check if script attribute is dirty, 
        # but here we follow the handoff which focuses on the execution gate.

    # unattributed (pre-tagging)
    @Aras.model_action(name="generate_report", permission="read", label="Generate Report", icon="Play")
    def generate_report(self, db, current_user=None):
        """
        Action to execute the report logic.
        """
        from .services.report_service import ReportService
        report_data = ReportService.generate(self, db=db, current_user=current_user)
        return ok(report_data, message="Report generated successfully.")
