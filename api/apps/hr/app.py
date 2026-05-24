from core import Aras
from . import models

class HR(Aras.App):
    app_name = "hr"
    table_prefix = "erp_hr"
    app_label = "Human Resources"
    icon = "Users"
    models = [models.Department, models.Position, models.Employee]
