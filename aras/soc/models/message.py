from arasCore.lib.core.base_model import ArasSoftModel, db


class SocMessage(ArasSoftModel):
    __tablename__ = "soc_message"
    __soft_delete__ = True
    __table_args__ = (
        db.Index("idx_message_conv", "conversation_id", "created_at"),
    )

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    conversation_id = db.Column(db.Integer, db.ForeignKey("soc_conversation.id"), nullable=False)
    sender_id       = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    content         = db.Column(db.Text, nullable=False)
    message_type    = db.Column(db.String(10), default="text")   # text/image/file
    media_url       = db.Column(db.String(500), nullable=True)

    __serialize_relations__ = {"sender_username": ("sender", "username")}

    sender = db.relationship("User", foreign_keys=[sender_id], backref=db.backref("soc_messages_sent", lazy="dynamic"))
