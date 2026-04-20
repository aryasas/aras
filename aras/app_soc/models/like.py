from arasCore.lib.base_model import ArasSoftModel, db


class SocLike(ArasSoftModel):
    __tablename__ = "soc_like"
    __soft_delete__ = True
    __table_args__ = (
        db.UniqueConstraint("user_id", "target_type", "target_id", name="uq_like"),
        db.Index("idx_like_target", "target_type", "target_id"),
    )

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    user_id     = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    target_type = db.Column(db.String(10), nullable=False)   # post / comment
    target_id   = db.Column(db.Integer, nullable=False)
    reaction    = db.Column(db.String(10), default="like")   # like/love/haha/wow/sad/angry

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("soc_likes", lazy="dynamic"))
