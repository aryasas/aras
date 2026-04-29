from arasCore.lib.core.base_model import ArasSoftModel, db


class SocComment(ArasSoftModel):
    __tablename__ = "soc_comment"
    __soft_delete__ = True
    __table_args__ = (
        db.Index("idx_comment_post", "post_id", "created_at"),
        db.Index("idx_comment_parent", "parent_id"),
    )

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    post_id    = db.Column(db.Integer, db.ForeignKey("soc_post.id"), nullable=False)
    author_id  = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    parent_id  = db.Column(db.Integer, db.ForeignKey("soc_comment.id"), nullable=True)
    content    = db.Column(db.Text, nullable=False)
    like_count = db.Column(db.Integer, default=0)

    __serialize_relations__ = {"author_username": ("author", "username")}

    author  = db.relationship("User", foreign_keys=[author_id],
                              backref=db.backref("soc_comments", lazy="dynamic"))
    replies = db.relationship("SocComment", backref=db.backref("parent", remote_side="SocComment.id"),
                              lazy="dynamic", foreign_keys="SocComment.parent_id")
