from core import Aras
from .models import Product, Customer, Order, Category, ProductCategory
from . import views # Register Views
from . import schemas # Register Schemas

class ErpApp(Aras.App):
    app_name = "erp"
    app_label = "ERP System"
    description = "Core ERP modules including Products and Customers."
    icon = "Briefcase"
    
    models = [Product, Customer, Order, Category, ProductCategory]
