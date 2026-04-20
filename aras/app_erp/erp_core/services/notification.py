"""core.notification — create in-app notifications."""
from arasCore.lib.extensions import db
from aras.app_erp.erp_core.models.notification import CoreNotification


def send(user_id: int, type: str, title: str, body: str = None,
         url: str = None, company_id: int = None):
    notif = CoreNotification(
        user_id=user_id,
        company_id=company_id,
        type=type,
        title=title,
        body=body,
        url=url,
    )
    db.session.add(notif)
    db.session.flush()
    return notif


def mark_read(notif_id: int, user_id: int):
    n = CoreNotification.query.filter_by(id=notif_id, user_id=user_id).first()
    if n:
        n.is_read = True
        db.session.flush()


def mark_all_read(user_id: int, company_id: int = None):
    q = CoreNotification.query.filter_by(user_id=user_id, is_read=False)
    if company_id:
        q = q.filter_by(company_id=company_id)
    q.update({"is_read": True})
