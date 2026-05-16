from core import Aras
from ..app import ERP
from . import models

class HRApp(Aras.App):
    app_name = "hr"
    parent_name = "erp"
    app_label = "Human Resources"
    models = [models.Department, models.Position, models.Employee]
