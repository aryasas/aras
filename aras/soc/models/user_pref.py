from arasCore.lib.core.base_model import ArasModel, db


class SocUserPref(ArasModel):
    __tablename__ = "soc_user_pref"

    # id, is_active, created_at, updated_at, created_by_id, updated_by_id — from ArasModel
    user_id             = db.Column(db.Integer, db.ForeignKey("auth_users.id"), unique=True, nullable=False)
    notif_like          = db.Column(db.Boolean, default=True)
    notif_comment       = db.Column(db.Boolean, default=True)
    notif_friend_req    = db.Column(db.Boolean, default=True)
    notif_friend_accept = db.Column(db.Boolean, default=True)
    notif_mention       = db.Column(db.Boolean, default=True)
    notif_share         = db.Column(db.Boolean, default=True)
    notif_email_digest  = db.Column(db.Boolean, default=False)
    allow_search        = db.Column(db.Boolean, default=True)
    allow_message_from  = db.Column(db.String(10), default="friends")  # all/friends/none
    theme               = db.Column(db.String(10), default="light")

    user = db.relationship("User", foreign_keys=[user_id], backref=db.backref("soc_pref", uselist=False))
