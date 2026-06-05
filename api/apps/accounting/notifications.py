# gpt-5
from datetime import datetime, timezone
import logging

from core import Aras

logger = logging.getLogger(__name__)


# gpt-5
def _send_email(db, recipient: str, subject: str, text: str, html: str) -> None:
    from apps.saas.services.email import get_transport

    get_transport(db=db).send(recipient, subject, text=text, html=html)


# gpt-5
def send_overdue_ar_digest() -> None:
    from core.workspace.models import Organization
    from .services.payment import PaymentService

    db = next(Aras.get_db())
    try:
        orgs = db.query(Organization).all()
        for org in orgs:
            recipient = getattr(org, "email", None)
            if not recipient:
                logger.warning("Skipping overdue AR digest for org %s: no notification email", org.id)
                continue

            overdue_invoices = PaymentService.get_overdue_invoices(db, org.id)
            if not overdue_invoices:
                continue

            generated_at = datetime.now(timezone.utc).isoformat()
            subject = f"Overdue receivables digest for {org.name}"
            text_lines = [
                f"- {invoice.number}: due {invoice.due_date.isoformat()} outstanding {invoice.amount_due:.2f}"
                for invoice in overdue_invoices
            ]
            html_lines = [
                f"<li>{invoice.number}: due {invoice.due_date.isoformat()} outstanding {invoice.amount_due:.2f}</li>"
                for invoice in overdue_invoices
            ]
            text = (
                f"Overdue receivables digest for {org.name}\n"
                f"Generated at: {generated_at}\n\n"
                + "\n".join(text_lines)
            )
            html = (
                f"<p>Overdue receivables digest for <strong>{org.name}</strong></p>"
                f"<p>Generated at: {generated_at}</p>"
                f"<ul>{''.join(html_lines)}</ul>"
            )
            _send_email(db, recipient, subject, text, html)
    finally:
        db.close()


# gpt-5
def send_payment_confirmation(db, payment) -> None:
    from apps.party.models import Party

    if payment.party_id is None:
        return

    party = db.get(Party, payment.party_id)
    recipient = getattr(party, "email", None) if party else None
    if not recipient:
        logger.warning("Skipping payment confirmation for %s: no party email", payment.id)
        return

    subject = f"Payment confirmation {payment.number}"
    posted_at = datetime.now(timezone.utc).isoformat()
    text = (
        f"Payment {payment.number} has been recorded.\n"
        f"Amount: {float(payment.amount or 0):.2f}\n"
        f"Status: {payment.status}\n"
        f"Recorded at: {posted_at}\n"
    )
    html = (
        f"<p>Payment <strong>{payment.number}</strong> has been recorded.</p>"
        f"<p>Amount: {float(payment.amount or 0):.2f}<br>Status: {payment.status}<br>Recorded at: {posted_at}</p>"
    )
    _send_email(db, recipient, subject, text, html)
