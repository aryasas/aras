# gemini-2-5-flash
from core import Aras
from ..models import Subscription, SaaSInvoice, SaaSPayment
from datetime import datetime, timedelta
import logging

class BillingService(Aras):
    @classmethod
    def generate_due_invoices(cls, db):
        now = datetime.now()
        due_subs = db.query(Subscription).filter(
            Subscription.status == "active",
            Subscription.next_billing_at <= now
        ).all()
        
        for sub in due_subs:
            # Create Invoice
            invoice_num = f"INV-{sub.id}-{now.strftime('%Y%m%d%H%M')}"
            invoice = SaaSInvoice(
                subscription_id=sub.id,
                number=invoice_num,
                period_start=sub.next_billing_at,
                period_end=sub.next_billing_at + timedelta(days=30),
                amount=sub.plan.price,
                currency=sub.plan.currency,
                status="unpaid",
                due_at=now + timedelta(days=7)
            )
            db.add(invoice)
            
            # Advance next_billing_at
            sub.next_billing_at = sub.next_billing_at + timedelta(days=30)
            
        db.commit()

    @classmethod
    def enforce_overdue(cls, db):
        now = datetime.now()
        overdue_invoices = db.query(SaaSInvoice).filter(
            SaaSInvoice.status == "unpaid",
            SaaSInvoice.due_at + timedelta(days=7) <= now
        ).all()
        
        for inv in overdue_invoices:
            inv.status = "overdue"
            sub = inv.subscription
            if sub and sub.status == "active":
                sub.status = "suspended"
                # Revoke license logic
                from ..services.license_service import LicenseService
                from ..models import LicenseToken
                token_obj = db.query(LicenseToken).filter_by(subscription_id=sub.id, revoked=False).first()
                if token_obj:
                    LicenseService.revoke_license(db, token_obj.id)
        db.commit()

    @classmethod
    def send_dunning_emails(cls, db):
        # claude-sonnet-4-6
        from .email import get_transport
        
        now = datetime.now()
        # Invoices overdue by more than 1 day but less than 7 days
        unpaid_invoices = db.query(SaaSInvoice).filter(
            SaaSInvoice.status == "unpaid",
            SaaSInvoice.due_at < now,
            SaaSInvoice.due_at > now - timedelta(days=7)
        ).all()
        
        transport = get_transport()
        for inv in unpaid_invoices:
            sub = inv.subscription
            if not sub or not sub.email:
                continue
                
            subject = f"Action Required: Your Aras invoice {inv.number} is overdue"
            text = f"""
Hi {sub.full_name or sub.company_name},

Your invoice {inv.number} for {inv.amount} {inv.currency} is overdue. 
Please pay it to avoid service interruption.

Best regards,
Aras Team
"""
            html = f"""
<p>Hi {sub.full_name or sub.company_name},</p>
<p>Your invoice <strong>{inv.number}</strong> for {inv.amount} {inv.currency} is overdue.</p>
<p>Please pay it to avoid service interruption.</p>
<p>Best regards,<br>Aras Team</p>
"""
            
            transport.send(sub.email, subject, html=html, text=text)
            logging.info(f"Dunning email sent for invoice {inv.number} to {sub.email}")
