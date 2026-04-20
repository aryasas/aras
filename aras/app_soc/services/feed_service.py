from aras.app_soc.models import SocPost, SocFriendship
from arasCore.lib.extensions import db


def get_feed(user_id, page=1, per_page=20):
    """Return paginated feed: own posts + accepted friends' posts."""
    friend_ids = db.session.query(SocFriendship.to_user_id).filter(
        SocFriendship.from_user_id == user_id,
        SocFriendship.status == "accepted",
        SocFriendship.deleted_at.is_(None),
    ).union(
        db.session.query(SocFriendship.from_user_id).filter(
            SocFriendship.to_user_id == user_id,
            SocFriendship.status == "accepted",
            SocFriendship.deleted_at.is_(None),
        )
    ).subquery()

    return (
        SocPost.query
        .filter(
            SocPost.deleted_at.is_(None),
            db.or_(
                SocPost.author_id == user_id,
                db.and_(
                    SocPost.author_id.in_(db.session.query(friend_ids)),
                    SocPost.visibility.in_(["public", "friends"]),
                ),
            ),
        )
        .order_by(SocPost.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )


def get_public_feed(page=1, per_page=20):
    return (
        SocPost.query
        .filter(SocPost.deleted_at.is_(None), SocPost.visibility == "public")
        .order_by(SocPost.created_at.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
