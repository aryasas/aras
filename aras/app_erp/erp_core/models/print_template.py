from arasCore.lib.base_model import ArasModel, db


class PrintTemplate(ArasModel):
    __tablename__ = "print_template"
    __table_args__ = (
        db.UniqueConstraint("company_id", "doc_type", "code", name="uq_print_template"),
    )

    company_id    = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
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

    versions = db.relationship("PrintTemplateVersion", backref="template", lazy="dynamic",
                               cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PrintTemplate {self.doc_type}/{self.code}>"


class PrintTemplateVersion(ArasModel):
    __tablename__ = "print_template_version"

    template_id = db.Column(db.Integer, db.ForeignKey("print_template.id"), nullable=False)
    version_no  = db.Column(db.Integer, nullable=False)
    body_html   = db.Column(db.Text, nullable=False)
    css         = db.Column(db.Text, nullable=True)
