from core import Aras
from core.logic.discovery import autodiscover_models
from . import views  # noqa: F401

from core.registry.config_registry import ConfigSection, ConfigField
from core.registry.master_data_registry import MasterEntity
from .models import Department, Position

class HR(Aras.App):
    app_name = "hr"
    app_label = "Human Resources"
    icon = "Users"

    master_data = [
        MasterEntity(key="department", model=Department, scope="module", icon="Users", order=10),
        MasterEntity(key="position", model=Position, scope="module", icon="Briefcase", order=20),
    ]

    config_sections = [
        ConfigSection(key="general", label="General", scope="module", fields=[
            ConfigField(key="workweek_days", type="number", default=5, label="Workweek Days", help="1-7"),
            ConfigField(key="standard_hours_per_day", type="number", default=8, label="Standard Hours per Day"),
            ConfigField(key="payroll_currency", type="string", default="USD", label="Payroll Currency"),
            ConfigField(key="annual_leave_days", type="number", default=12, label="Annual Leave Days"),
        ]),
        ConfigSection(key="attendance", label="Attendance", scope="module", fields=[
            ConfigField(key="enable_geo_checkin", type="bool", default=False, label="Enable Geo Check-In"),
            ConfigField(key="late_grace_minutes", type="number", default=15, label="Late Grace Period (minutes)"),
        ]),
    ]
    models = autodiscover_models(__name__, ["models"])
