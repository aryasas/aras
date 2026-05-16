from core import Aras
from .models import Lead, Pipeline, Stage, Activity

class PipelineView(Aras.View):
    model = Pipeline
    title = "Pipelines"
    icon = "pi pi-sitemap"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "stages"],
        },
    ]

class LeadView(Aras.View):
    model = Lead
    title = "Leads & Opportunities"
    icon = "pi pi-filter"
    layout = [
        {"title": "Identity", "fields": ["lead_type", "name", "party_id", "status"]},
        {"title": "Contact", "fields": ["contact_name", "contact_email", "contact_phone"]},
        {"title": "Sales", "fields": ["pipeline_id", "stage_id", "salesperson_id", "expected_revenue", "probability", "priority"]},
        {"title": "Activities", "fields": ["activities"]},
        {"title": "Description", "fields": ["description"]}
    ]

class ActivityView(Aras.View):
    model = Activity
    title = "Sales Activities"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name", "type", "lead_id", "scheduled_date", "notes"],
        },
    ]


