from datetime import datetime
from arasCore.lib.core.extensions import db
from aras.soc.models import SocFriendship, SocProfile


def get_friendship(user_id, other_id):
    return SocFriendship.query.filter(
        db.or_(
            db.and_(SocFriendship.from_user_id == user_id, SocFriendship.to_user_id == other_id),
            db.and_(SocFriendship.from_user_id == other_id, SocFriendship.to_user_id == user_id),
        ),
        SocFriendship.deleted_at.is_(None),
    ).first()


def send_request(from_user_id, to_user_id):
    existing = get_friendship(from_user_id, to_user_id)
    if existing:
        return existing, False
    f = SocFriendship(from_user_id=from_user_id, to_user_id=to_user_id, status="pending")
    db.session.add(f)
    db.session.commit()
    return f, True


def accept_request(from_user_id, to_user_id):
    f = SocFriendship.query.filter_by(
        from_user_id=from_user_id, to_user_id=to_user_id, status="pending"
    ).first()
    if not f:
        return None
    f.status = "accepted"
    f.updated_at = datetime.utcnow()
    _increment_friend_count(from_user_id)
    _increment_friend_count(to_user_id)
    db.session.commit()
    return f


def reject_request(from_user_id, to_user_id):
    f = SocFriendship.query.filter_by(
        from_user_id=from_user_id, to_user_id=to_user_id, status="pending"
    ).first()
    if not f:
        return None
    f.status = "rejected"
    f.updated_at = datetime.utcnow()
    db.session.commit()
    return f


def unfriend(user_id, other_id):
    f = get_friendship(user_id, other_id)
    if f and f.status == "accepted":
        f.deleted_at = datetime.utcnow()
        _decrement_friend_count(user_id)
        _decrement_friend_count(other_id)
        db.session.commit()


def block_user(blocker_id, blocked_id):
    f = get_friendship(blocker_id, blocked_id)
    if f:
        if f.status == "accepted":
            _decrement_friend_count(blocker_id)
            _decrement_friend_count(blocked_id)
        f.status = "blocked"
        f.from_user_id = blocker_id
        f.to_user_id = blocked_id
    else:
        f = SocFriendship(from_user_id=blocker_id, to_user_id=blocked_id, status="blocked")
        db.session.add(f)
    db.session.commit()


def get_friends(user_id):
    sent = SocFriendship.query.filter_by(from_user_id=user_id, status="accepted").filter(
        SocFriendship.deleted_at.is_(None)).all()
    received = SocFriendship.query.filter_by(to_user_id=user_id, status="accepted").filter(
        SocFriendship.deleted_at.is_(None)).all()
    friend_ids = [f.to_user_id for f in sent] + [f.from_user_id for f in received]
    return friend_ids


def get_pending_requests(user_id):
    return SocFriendship.query.filter_by(to_user_id=user_id, status="pending").filter(
        SocFriendship.deleted_at.is_(None)).all()


def _increment_friend_count(user_id):
    p = SocProfile.query.filter_by(user_id=user_id).first()
    if p:
        p.friend_count = (p.friend_count or 0) + 1


def _decrement_friend_count(user_id):
    p = SocProfile.query.filter_by(user_id=user_id).first()
    if p and p.friend_count and p.friend_count > 0:
        p.friend_count -= 1
