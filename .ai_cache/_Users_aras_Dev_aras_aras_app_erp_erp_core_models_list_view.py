from datetime import datetime
from arasCore.lib.extensions import db


class ErpListViewSetting(db.Model):
    __tablename__ = "erp_list_view_setting"
    __table_args__ = (
        db.UniqueConstraint("user_id", "doctype", name="uq_list_view_user_doctype"),
    )

    id           = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    doctype      = db.Column(db.String(100), nullable=False)
    columns_json = db.Column(db.Text, nullable=True)
    filters_json = db.Column(db.Text, nullable=True)
    page_size    = db.Column(db.Integer, default=20, nullable=False)
    updated_at   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
