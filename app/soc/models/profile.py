from arasCore.lib.core.base_model import ArasSoftModel, db


class SocProfile(ArasSoftModel):
    __tablename__ = "soc_profile"
    __soft_delete__ = True

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id, deleted_at — from ArasModel
    user_id         = db.Column(db.Integer, db.ForeignKey("auth_users.id"), unique=True, nullable=False)
    avatar_url      = db.Column(db.String(500), nullable=True)
    cover_url       = db.Column(db.String(500), nullable=True)
    bio             = db.Column(db.Text, nullable=True)
    location        = db.Column(db.String(200), nullable=True)
    website         = db.Column(db.String(200), nullable=True)
    birth_date      = db.Column(db.Date, nullable=True)
    work            = db.Column(db.String(200), nullable=True)
    education       = db.Column(db.String(200), nullable=True)
    privacy_profile = db.Column(db.String(10), default="public")   # public/friends/private
    privacy_posts   = db.Column(db.String(10), default="friends")
    privacy_friends = db.Column(db.String(10), default="public")
    post_count      = db.Column(db.Integer, default=0)
    friend_count    = db.Column(db.Integer, default=0)

    __serialize_relations__ = {"username": ("user", "username")}

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("soc_profile", uselist=False))
