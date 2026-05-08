from arasCore.arasgen import ArasGen
from app.erp.erp_main.manifest import Main
from arasCore.lib.core.base_model import ArasModel, db


class PrintTemplate(ArasGen.Model, module=Main):
    __title__     = "Print Templates"
    __menu__      = "Reports"
    __icon__      = "fa-print"
    __menu_order__= 0
    __tablename__ = "main_print_template"
    __table_args__ = (
        db.UniqueConstraint("company_id", "doc_type", "code", name="uq_print_template"),
    )

    company_id    = db.Column(db.Integer, db.ForeignKey("cfg_company.id"), nullable=False)
    doc_type      = db.Column(db.String(50), nullable=False)   # 'sales.invoice', 'hr.payslip'
    code          = db.Column(db.String(50), nullable=False)
    name          = db.Column(db.String(150), nullable=False)
    engine        = db.Column(db.String(20), default="jinja_html")
    paper_size    = db.Column(db.String(20), default="A4")
    orientation   = db.Column(db.String(10), default="portrait")
    margin_top    = db.Column(db.SmallInteger, default=10)
    margin_right  = db.Column(db.SmallInteger, default=10)
    margin_bottom = db.Column(db.SmallInteger, default=10)
    margin_left   = db.Column(db.SmallInteger, default=10)
    header_html   = db.Column(db.Text, nullable=True)
    body_html     = db.Column(db.Text, nullable=False, default="")
    footer_html   = db.Column(db.Text, nullable=True)
    css           = db.Column(db.Text, nullable=True)
    is_default    = db.Column(db.Boolean, default=False)

    versions = db.relationship("PrintTemplateVersion", back_populates="template", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PrintTemplate {self.doc_type}/{self.code}>"


class PrintTemplateVersion(ArasGen.Model, module=Main):
    __tablename__ = "main_print_template_version"

    template_id = db.Column(db.Integer, db.ForeignKey("main_print_template.id"), nullable=False)
    version_no  = db.Column(db.Integer, nullable=False)
    body_html   = db.Column(db.Text, nullable=False)
    css         = db.Column(db.Text, nullable=True)

    template = db.relationship("PrintTemplate", back_populates="versions")
