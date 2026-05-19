import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from core import Aras
from core.auth.license import issue_license_token
from ..models import LicenseToken, Subscription

class LicenseService(Aras.Service):
    @staticmethod
    def issue_license(db: Session, subscription_id: int, expiry_days: int = 30) -> str:
        sub = db.query(Subscription).filter_by(id=subscription_id).first()
        if not sub:
            raise ValueError("Subscription not found")
        
        token_str = issue_license_token(sub.tenant_id, expiry_days)
        
        token_doc = LicenseToken(
            subscription_id=subscription_id,
            token=token_str,
            issued_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=expiry_days)
        )
        db.add(token_doc)
        db.commit()
        return token_str
        
    @staticmethod
    def revoke_license(db: Session, license_id: int):
        token_doc = db.query(LicenseToken).filter_by(id=license_id).first()
        if token_doc:
            token_doc.revoked = True
            db.commit()
            
    @staticmethod
    def renew_license(db: Session, subscription_id: int) -> str:
        old_tokens = db.query(LicenseToken).filter_by(subscription_id=subscription_id, revoked=False).all()
        for t in old_tokens:
            t.revoked = True
        
        return LicenseService.issue_license(db, subscription_id, 30)
