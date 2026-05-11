from arasCore.arasgen import ArasGen
from app.erp.erp_crm.manifest import Crm


class CrmCustomerGroup(ArasGen.Model, module=Crm):
    __tablename__ = "crm_customer_group"
    __title__     = "Customer Group"
    __icon__      = "fa-users"
    __menu_order__= 3
    __display_fields__ = ("name",)

    name = ArasGen.String(null=False, unique=True, length=100, label="Name")

    def __repr__(self):
        return f"<CrmCustomerGroup {self.name}>"
