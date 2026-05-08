from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class CoreCustomField(ArasGen.Model, module=Main):
    __tablename__ = "main_custom_field"
    __table_args__ = (
        db.UniqueConstraint("company_id", "target_model", "field_key", name="uq_custom_field"),
    )

    company_id    = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)
    target_model  = db.Column(db.String(100), nullable=False)  # 'inv.product', 'sal.customer'
    field_key     = db.Column(db.String(50), nullable=False)
    label         = db.Column(db.String(150), nullable=False)
    ftype         = db.Column(db.String(20), default="string")  # string/int/decimal/date/bool/select/fk/text
    required      = db.Column(db.Boolean, default=False)
    options_json  = db.Column(db.JSON, nullable=True)
    default_value = db.Column(db.String(255), nullable=True)
    sequence      = db.Column(db.Integer, default=10)

    def __repr__(self):
        return f"<CoreCustomField {self.target_model}.{self.field_key}>"
