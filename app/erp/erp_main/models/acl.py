from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db
from arasCore.auth import User


class ErpRole(ArasGen.Model, module=Main):
    __title__     = "Roles"
    __icon__      = "fa-shield"
    __menu_order__= 0
    __tablename__ = "main_role"

    company_id  = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=True)  # NULL=global
    code        = db.Column(db.String(50), nullable=False)
    name        = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_system   = db.Column(db.Boolean, default=False)

    permissions = db.relationship("ErpRolePermission", backref="role", lazy="dynamic",
                                  cascade="all, delete-orphan")

    def has_permission(self, perm_code):
        return any(rp.permission.code == perm_code for rp in self.permissions)

    def __repr__(self):
        return f"<ErpRole {self.code}>"


class ErpPermission(ArasGen.Model, module=Main):
    __title__     = "Permissions"
    __icon__      = "fa-key"
    __menu_order__= 0
    __tablename__ = "main_permission"

    code   = db.Column(db.String(100), unique=True, nullable=False)
    label  = db.Column(db.String(200), nullable=True)
    module = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f"<ErpPermission {self.code}>"


class ErpRolePermission(db.Model):
    __tablename__ = "main_role_permission"
    __table_args__ = (
        db.PrimaryKeyConstraint("role_id", "permission_id"),
    )

    role_id       = db.Column(db.Integer, db.ForeignKey("main_role.id"), nullable=False)
    permission_id = db.Column(db.Integer, db.ForeignKey("main_permission.id"), nullable=False)

    permission = db.relationship("ErpPermission")


class ErpUserCompany(db.Model):
    __tablename__ = "main_user_company"
    __table_args__ = (
        db.PrimaryKeyConstraint("user_id", "company_id"),
    )

    user_id    = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    role_id    = db.Column(db.Integer, db.ForeignKey("main_role.id"), nullable=True)
    is_default = db.Column(db.Boolean, default=False)

    user    = db.relationship(User, foreign_keys=[user_id], backref=db.backref("company_memberships", lazy="dynamic"))
    company = db.relationship("Company", backref=db.backref("members", lazy="dynamic"))
    role    = db.relationship("ErpRole")
