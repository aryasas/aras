from arasCore.lib.core.base_model import ArasModel, db


class SocConversation(ArasModel):
    __tablename__ = "soc_conversation"

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id — from ArasModel
    last_message_at = db.Column(db.DateTime, nullable=True)

    participants = db.relationship("SocConversationParticipant", backref="conversation",
                                   lazy="dynamic", cascade="all, delete-orphan")
    messages     = db.relationship("SocMessage", backref="conversation", lazy="dynamic",
                                   cascade="all, delete-orphan")

    def get_other_participant(self, user_id):
        return self.participants.filter(
            SocConversationParticipant.user_id != user_id
        ).first()


class SocConversationParticipant(ArasModel):
    __tablename__ = "soc_conversation_participant"
    __table_args__ = (
        db.UniqueConstraint("conversation_id", "user_id", name="uq_participant"),
    )

    # id, created_at, updated_at, created_by_id — from ArasModel
    conversation_id = db.Column(db.Integer, db.ForeignKey("soc_conversation.id"), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    last_read_at    = db.Column(db.DateTime, nullable=True)
    joined_at       = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("soc_conversations", lazy="dynamic"))
