from arasCore.lib.core.base_model import ArasSoftModel, db


class SocPost(ArasSoftModel):
    __tablename__ = "soc_post"
    __soft_delete__ = True
    __table_args__ = (
        db.Index("idx_post_author", "author_id", "created_at"),
        db.Index("idx_post_feed", "created_at"),
    )

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    author_id      = db.Column(db.Integer, db.ForeignKey("auth_users.id"), nullable=False)
    content        = db.Column(db.Text, nullable=False)
    visibility     = db.Column(db.String(10), default="friends")  # public/friends/private
    is_edited      = db.Column(db.Boolean, default=False)
    shared_from_id = db.Column(db.Integer, db.ForeignKey("soc_post.id"), nullable=True)
    like_count     = db.Column(db.Integer, default=0)
    comment_count  = db.Column(db.Integer, default=0)
    share_count    = db.Column(db.Integer, default=0)

    __serialize_relations__ = {"author_username": ("author", "username")}

    author      = db.relationship("User", foreign_keys=[author_id],
                                  backref=db.backref("soc_posts", lazy="dynamic"))
    shared_from = db.relationship("SocPost", remote_side="SocPost.id", foreign_keys=[shared_from_id])
    media       = db.relationship("SocPostMedia", backref="post", lazy="dynamic",
                                  cascade="all, delete-orphan")
    comments    = db.relationship("SocComment", backref="post", lazy="dynamic",
                                  primaryjoin="and_(SocComment.post_id==SocPost.id, SocComment.deleted_at==None)",
                                  cascade="all, delete-orphan")


class SocPostMedia(ArasSoftModel):
    __tablename__ = "soc_post_media"
    __soft_delete__ = False

    # id, created_at, updated_at, created_by_id — from ArasModel
    post_id    = db.Column(db.Integer, db.ForeignKey("soc_post.id"), nullable=False)
    media_url  = db.Column(db.String(500), nullable=False)
    media_type = db.Column(db.String(10), default="image")  # image/video
    sequence   = db.Column(db.SmallInteger, default=0)
