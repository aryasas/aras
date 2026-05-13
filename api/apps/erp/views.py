from core import Aras
from .models import Product, Customer

class ProductView(Aras.View):
    model = Product
    title = "Product Catalog"
    fields = {
        "name": {"label": "Product Name", "searchable": True},
        "sku": {"label": "SKU / Item Code"},
        "price": {"label": "Standard Price", "ui_type": "currency"},
        "description": {"label": "Description", "ui_type": "textarea"},
        "stock_quantity": {"label": "Current Stock"}
    }

class CustomerView(Aras.View):
    model = Customer
    title = "Customer Relationship"
    fields = {
        "name": {"label": "Customer Name", "searchable": True},
        "email": {"label": "Email", "ui_type": "email"},
        "address": {"label": "Address", "ui_type": "textarea"}
    }
