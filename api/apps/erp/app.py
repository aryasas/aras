from core import Aras
from .models import Product, Customer

class ErpApp(Aras.App):
    app_name = "erp"
    app_label = "ERP System"
    description = "Core ERP modules including Products and Customers."
    icon = "Briefcase"
    
    models = [Product, Customer]
