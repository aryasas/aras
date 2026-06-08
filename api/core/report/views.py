from core import Aras
from .models import Report

class ReportView(Aras.View):
    model = Report
    title = "Reports"
    icon = "FileDigit"
    layout = [
        {"title": "Identity", "fields": ["code", "name", "module", "report_type"]},
        {"title": "Query Config", "fields": ["linked_doctype", "query_filters"]},
        {"title": "Display", "fields": ["columns_json", "filters_json"]}
    ]
