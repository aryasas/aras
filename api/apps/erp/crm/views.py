from core import Aras
from .models import Customer, Contact, Lead, Pipeline, Stage, Activity


class CustomerView(Aras.View):
    model = Customer
    title = "Customers"
    layout = [
        {"title": "General", "fields": ["name", "code", "tax_id"]},
        {"title": "Contact", "fields": ["email", "phone", "mobile", "address"]},
        {"title": "Settings", "fields": ["pricelist_id"]},
        {"title": "Contacts", "fields": ["contacts"]}
    ]

class ContactView(Aras.View):
    model = Contact
    title = "Contacts"

class PipelineView(Aras.View):
    model = Pipeline
    title = "Pipelines"
    icon = "pi pi-sitemap"

class LeadView(Aras.View):
    model = Lead
    title = "Leads & Opportunities"
    icon = "pi pi-filter"
    layout = [
        {"title": "Identity", "fields": ["lead_type", "name", "customer_id", "status"]},
        {"title": "Contact", "fields": ["contact_name", "contact_email", "contact_phone"]},
        {"title": "Sales", "fields": ["pipeline_id", "stage_id", "salesperson_id", "expected_revenue", "probability", "priority"]},
        {"title": "Activities", "fields": ["activities"]},
        {"title": "Description", "fields": ["description"]}
    ]

class ActivityView(Aras.View):
    model = Activity
    title = "Sales Activities"


