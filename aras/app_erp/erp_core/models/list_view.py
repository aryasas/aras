from arasCore.lib.base_model import ArasModel, db


class ErpListViewSetting(ArasModel):
    __tablename__ = "erp_list_view_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "doctype", name="uq_list_view_user_doctype"),
    )

    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    doctype      = db.Column(db.String(100), nullable=False)
    columns_json = db.Column(db.Text, nullable=True)
    filters_json = db.Column(db.Text, nullable=True)
    page_size    = db.Column(db.Integer, default=20, nullable=False)
    # "list" = standard admin list view, "report" = report view
    view_mode    = db.Column(db.String(10), default="list", nullable=False)
    show_totals  = db.Column(db.Boolean, default=False, nullable=False)


class ErpReportSetting(ArasModel):
    """Per-user saved defaults for a specific report (date preset, params, per_page)."""
    __tablename__ = "erp_report_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "report_id", name="uq_report_setting"),
    )

    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    report_id    = db.Column(db.Integer, db.ForeignKey("erp_report.id"), nullable=False)
    # date_preset: "today","this_week","this_month","this_year","custom"
    date_preset  = db.Column(db.String(20), default="this_month", nullable=False)
    date_from    = db.Column(db.String(20), nullable=True)   # used when preset="custom"
    date_to      = db.Column(db.String(20), nullable=True)
    params_json  = db.Column(db.Text, nullable=True)         # JSON: other filter defaults
    per_page     = db.Column(db.Integer, default=50, nullable=False)
