# -*- coding: utf-8 -*-
from datetime import datetime
from arasCore.lib.core.extensions import db
from arasCore.lib.core.base_model import ArasModel

_ORIGIN_MODEL_REGISTRY: dict = {}


def register_origin_model(tablename: str, model_cls) -> None:
    _ORIGIN_MODEL_REGISTRY[tablename] = model_cls


class DeletedDoc(ArasModel):
    __tablename__ = "aras_deleted_doc"
    __table_args__ = (
        db.Index("idx_deleted_doc_group",    "group_id"),
        db.Index("idx_deleted_doc_type_id",  "doc_type", "doc_id"),
    )

    id              = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    group_id        = db.Column(db.String(36),  nullable=False)
    parent_group_id = db.Column(db.String(36),  nullable=True)
    deleted_at      = db.Column(db.DateTime,    nullable=False, default=datetime.utcnow)
    deleted_by_id   = db.Column(db.Integer,     db.ForeignKey("auth_users.id"), nullable=True)

    doc_type        = db.Column(db.String(120), nullable=False)
    doc_id          = db.Column(db.BigInteger,  nullable=False)
    doc_data        = db.Column(db.JSON,        nullable=False)
    depth           = db.Column(db.Integer,     nullable=False, default=0)

    app_slug        = db.Column(db.String(80),  nullable=True)
    resource_slug   = db.Column(db.String(200), nullable=True)
    admin_url       = db.Column(db.String(300), nullable=True)

    deleted_by = db.relationship("User", foreign_keys=[deleted_by_id])
