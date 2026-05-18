from ..app import ERP
from . import models

class HR(ERP):
    app_name = "erp_hr"
    app_type = "module"
    app_label = "Human Resources"
    icon = "Users"
    models = [models.Department, models.Position, models.Employee]
