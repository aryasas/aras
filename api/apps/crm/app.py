from core import Aras
from core.registry.config_registry import ConfigSection, ConfigField
from core.registry.master_data_registry import MasterEntity
from .models import Lead, Pipeline, Stage, Activity

class CRM(Aras.App):
    app_name = "crm"
    app_label = "CRM"
    icon = "Users"
    saas_module = "crm"

    master_data = [
        MasterEntity(key="pipeline", model=Pipeline, scope="module", icon="GitBranch", order=10),
    ]

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="default_lead_source", type="string", default="website", label="Default Lead Source"),
            ConfigField(key="lead_aging_days", type="number", default=30, label="Lead Aging (days)"),
            ConfigField(key="enable_lead_scoring", type="bool", default=False, label="Enable Lead Scoring"),
        ]),
        ConfigSection(key="pipeline", label="Pipeline", scope="module", fields=[
            ConfigField(key="stale_deal_days", type="number", default=14, label="Stale Deal Threshold (days)"),
            ConfigField(key="auto_close_stale", type="bool", default=False, label="Auto-Close Stale Deals"),
        ]),
    ]
    
    models = [Lead, Pipeline, Stage, Activity]

    
    menu_groups = [
        {
            "label": "Sales Force",
            "icon": "Users",
            "models": ["crm_leads", "crm_pipelines"]
        },
        {
            "label": "Master Data",
            "icon": "Database",
            "models": []
        }
    ]

