from arasCore.arasgen import ArasGen
from app.erp.erp_sup.manifest import Sup


class SupSupplierGroup(ArasGen.Model, module=Sup):
    __tablename__ = "sup_supplier_group"
    __title__     = "Supplier Group"
    __icon__      = "fa-users"
    __menu_order__= 4
    __display_fields__ = ("name",)

    name = ArasGen.String(null=False, unique=True, length=100, label="Name")

    def __repr__(self):
        return f"<SupSupplierGroup {self.name}>"
