# gemini-2-5-flash
from abc import ABC, abstractmethod
import os
import logging
import smtplib
from email.message import EmailMessage
import requests
from typing import Optional

from core import Aras

# claude-sonnet-4-6
class EmailTransport(Aras, ABC):
    @abstractmethod
    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None):
        pass

# claude-sonnet-4-6
class ConsoleTransport(EmailTransport):
    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None):
        logging.info(f"[EMAIL CONSOLE] To: {to}")
        logging.info(f"[EMAIL CONSOLE] Subject: {subject}")
        if text:
            logging.info(f"[EMAIL CONSOLE] Text: {text[:100]}...")
        if html:
            logging.info(f"[EMAIL CONSOLE] HTML: {html[:100]}...")

# claude-sonnet-4-6
class SMTPTransport(EmailTransport):
    def __init__(self, db=None):
        self._db = db

    def _cfg(self, key: str, env_key: str, default: str = "") -> str:
        if self._db:
            try:
                from core.lib.config import ConfigService
                val = ConfigService.get(self._db, f"core.{key}")
                if val:
                    return str(val)
            except Exception:
                pass
        return os.getenv(env_key, default)

    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None):
        smtp_host = self._cfg("smtp_host", "SMTP_HOST")
        if not smtp_host:
            logging.error("SMTP_HOST not set for SMTPTransport")
            return

        smtp_port = int(self._cfg("smtp_port", "SMTP_PORT") or 587)
        smtp_user = self._cfg("smtp_user", "SMTP_USER")
        smtp_pass = self._cfg("smtp_password", "SMTP_PASS")
        smtp_from = self._cfg("smtp_from", "SMTP_FROM", "noreply@aras.com")

        msg = EmailMessage()
        if text:
            msg.set_content(text)
        if html:
            if text:
                msg.add_alternative(html, subtype='html')
            else:
                msg.set_content(html, subtype='html')
                
        msg["Subject"] = subject
        msg["From"] = smtp_from
        msg["To"] = to

        try:
            with smtplib.SMTP(smtp_host, smtp_port) as s:
                if smtp_user:
                    s.starttls()
                    s.login(smtp_user, smtp_pass)
                s.send_message(msg)
            logging.info(f"Email sent via SMTP to {to}")
        except Exception as e:
            logging.error(f"Failed to send email via SMTP to {to}: {e}")

# claude-sonnet-4-6
class ResendTransport(EmailTransport):
    def send(self, to: str, subject: str, html: Optional[str] = None, text: Optional[str] = None):
        api_key = os.getenv("RESEND_API_KEY")
        smtp_from = os.getenv("SMTP_FROM", "noreply@aras.com")
        
        if not api_key:
            logging.error("RESEND_API_KEY not set for ResendTransport")
            return

        payload = {
            "from": smtp_from,
            "to": to,
            "subject": subject,
        }
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
            
        try:
            response = requests.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            logging.info(f"Email sent via Resend to {to}")
        except Exception as e:
            logging.error(f"Failed to send email via Resend to {to}: {e}")

# claude-sonnet-4-6
def get_transport(db=None) -> EmailTransport:
    backend = os.getenv("EMAIL_BACKEND", "console").lower()
    if backend == "smtp":
        return SMTPTransport(db=db)
    elif backend == "resend":
        return ResendTransport()
    return ConsoleTransport()

# claude-sonnet-4-6
def send_setup_email(to_email: str, token: str, company_name: str, db=None):
    setup_url = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/portal/setup?token={token}"
    subject = f"Welcome to Aras! Complete your setup for {company_name}"
    text = f"""
    Hi,

    Thank you for choosing Aras. Your workspace for {company_name} is ready.
    
    Please click the link below to set your password and access your dashboard:
    {setup_url}
    
    This link will expire in 24 hours.
    
    Best regards,
    Aras Team
    """
    html = f"""
    <p>Hi,</p>
    <p>Thank you for choosing Aras. Your workspace for <strong>{company_name}</strong> is ready.</p>
    <p>Please click the link below to set your password and access your dashboard:</p>
    <p><a href="{setup_url}">{setup_url}</a></p>
    <p>This link will expire in 24 hours.</p>
    <p>Best regards,<br>Aras Team</p>
    """
    
    get_transport(db=db).send(to_email, subject, html=html, text=text)
