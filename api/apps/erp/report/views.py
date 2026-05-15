from core import Aras
from .models import Report

class ReportView(Aras.View):
    model = Report
    title = "Reports"
    icon = "pi pi-file-pdf"
    layout = [
        {"title": "Identity", "fields": ["code", "name", "module", "report_type", "linked_doctype"]},
        {"title": "Configuration", "fields": ["columns_json", "filters_json"]},
        {"title": "Script/Logic", "fields": ["script"]}
    ]
