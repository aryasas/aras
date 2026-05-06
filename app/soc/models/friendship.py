from arasCore.lib.core.base_model import ArasSoftModel, db


class SocFriendship(ArasSoftModel):
    __tablename__ = "soc_friendship"
    __soft_delete__ = True
    __table_args__ = (
        db.UniqueConstraint("from_user_id", "to_user_id", name="uq_friendship"),
        db.Index("idx_friendship_from", "from_user_id", "status"),
        db.Index("idx_friendship_to", "to_user_id", "status"),
    )

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    from_user_id = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    to_user_id   = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    status       = db.Column(db.String(10), nullable=False, default="pending")  # pending/accepted/rejected/blocked

    from_user = db.relationship("User", foreign_keys=[from_user_id],
                                backref=db.backref("friendships_sent", lazy="dynamic"))
    to_user   = db.relationship("User", foreign_keys=[to_user_id],
                                backref=db.backref("friendships_received", lazy="dynamic"))
