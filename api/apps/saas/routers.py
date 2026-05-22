from fastapi import APIRouter, Depends, HTTPException
from core.base.validation import Validation
from core.lib.database import get_db
from sqlalchemy.orm import Session
from .models import Subscription
from .services.license_service import LicenseService
from core.auth.license import verify_license_token

router = APIRouter(prefix="", tags=["SaaS Control Plane"])

class RenewLicenseRequest(Validation):
    tenant_id: str
    current_token: str

@router.post("/license/renew")
async def renew_license(data: RenewLicenseRequest, db: Session = Depends(get_db)):
    payload = verify_license_token(data.current_token)
    if not payload or payload.get("sub") != data.tenant_id:
        raise HTTPException(status_code=403, detail="Invalid token for this tenant")
    
    sub = db.query(Subscription).filter_by(tenant_id=data.tenant_id, status="active").first()
    if not sub:
        raise HTTPException(status_code=403, detail="No active subscription found")
        
    new_token = LicenseService.renew_license(db, sub.id)
    return {"token": new_token}
