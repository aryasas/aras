from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class Setting(ArasGen.Model, module=Main):
    __admin_list__= False
    __tablename__ = "main_setting"
    __table_args__ = (
        db.UniqueConstraint("scope", "scope_id", "key", name="uq_setting"),
    )

    scope       = db.Column(db.String(10), nullable=False, default="global")  # global/company/user
    scope_id    = db.Column(db.Integer, nullable=True)
    key         = db.Column(db.String(150), nullable=False)
    value_type  = db.Column(db.String(10), default="string")  # string/int/decimal/bool/json/date
    value       = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_secret   = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Setting {self.scope}:{self.key}>"
