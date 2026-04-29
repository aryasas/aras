"""core.notification — create in-app notifications."""
from arasCore.lib.core.extensions import db
from aras.erp.erp_core.models.notification import ErpNotification


def send(user_id: int, type: str, title: str, body: str = None,
         url: str = None, company_id: int = None):
    return ErpNotification.create({
        "user_id": user_id, "company_id": company_id,
        "type": type, "title": title, "body": body, "url": url,
    })


def mark_read(notif_id: int, user_id: int):
    n = ErpNotification.find(id=notif_id, user_id=user_id)
    if n:
        n.set_field("is_read", True)


def mark_all_read(user_id: int, company_id: int = None):
    q = ErpNotification.query.filter_by(user_id=user_id, is_read=False)
    if company_id:
        q = q.filter_by(company_id=company_id)
    q.update({"is_read": True})
