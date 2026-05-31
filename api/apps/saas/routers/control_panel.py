from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.base.validation import Validation
from typing import Optional
import os

from core.lib.database import get_db
from core.response import ok, err
from core.auth.service import require_admin
from core.tenant import service as tenant_service
from ..models import Subscription, SaaSPayment, LicenseToken
from ..services.metrics import MetricsService
from ..services.license_service import LicenseService

router = APIRouter(prefix="/control-panel", tags=["Control Panel"])

class ProvisionRequest(Validation):
    tenant_id: str
    db_name: Optional[str] = None

@router.get("/tenants")
def list_tenants(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    return ok(tenant_service.list_tenants(db))

@router.post("/tenants/provision", status_code=201)
def provision(body: ProvisionRequest, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    try:
        info = tenant_service.provision_tenant(db, body.tenant_id, db_name=body.db_name)
        return ok(info)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tenants/{tenant_id}/seed")
def seed(tenant_id: str, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    try:
        result = tenant_service.seed_tenant(db, tenant_id)
        return ok(result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/tenants/{tenant_id}")
def deprovision(tenant_id: str, db: Session = Depends(get_db), current_user=Depends(require_admin)):
    try:
        tenant_service.delete_tenant(db, tenant_id)
        return ok({"message": f"Tenant '{tenant_id}' deprovisioned."})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/tenants/{tenant_id}/metrics")
def get_tenant_metrics(tenant_id: str, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    metrics = MetricsService.tenant_usage(db, tenant_id)
    return ok(metrics)

@router.post("/tenants/{tenant_id}/ping")
def ping_tenant(tenant_id: str, current_user=Depends(require_admin)):
    # gemini-pro
    import httpx, os
    base = os.getenv("TENANT_BASE_URL_TEMPLATE", "http://{id}:8000").replace("{id}", tenant_id)
    try:
        r = httpx.get(f"{base}/api/v1/health", timeout=5)
        return {"tenant_id": tenant_id, "reachable": r.status_code == 200, "status": r.status_code}
    except Exception as e:
        return {"tenant_id": tenant_id, "reachable": False, "error": str(e)}

@router.get("/revenue")
def get_revenue(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    mrr = db.query(func.sum(SaaSPayment.amount)).filter(SaaSPayment.status == "succeeded").scalar() or 0
    return ok({
        "mrr": mrr,
        "arr": mrr * 12,
        "churn": 0,
        "active_tenants": db.query(func.count(Subscription.id)).filter(Subscription.status == "active").scalar()
    })

@router.get("/licenses")
def list_licenses(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    # list all tenant licenses
    licenses = db.query(LicenseToken).all()
    return ok(licenses)

class IssueLicenseRequest(Validation):
    tenant_id: str
    duration_days: int = 30

@router.post("/licenses/issue")
def handle_issue_license(body: IssueLicenseRequest, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    try:
        sub = db.query(Subscription).filter_by(tenant_id=body.tenant_id).first()
        if not sub:
            raise ValueError("Subscription not found")
        lic = LicenseService.issue_license(db, sub.id, body.duration_days)
        return ok({"token": lic})
    except Exception as e:
        return err(str(e))

@router.post("/licenses/{tenant_id}/renew")
def handle_renew_license(tenant_id: str, db: Session = Depends(get_db)):
    try:
        sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
        if not sub:
            raise ValueError("Subscription not found")
        lic = LicenseService.renew_license(db, sub.id)
        return ok({"token": lic})
    except Exception as e:
        return err(str(e))

@router.post("/licenses/{tenant_id}/revoke")
def handle_revoke_license(tenant_id: str, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    try:
        sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
        if not sub:
            raise ValueError("Subscription not found")
        tokens = db.query(LicenseToken).filter_by(subscription_id=sub.id, revoked=False).all()
        for t in tokens:
            t.revoked = True
        db.commit()
        return ok({"success": True})
    except Exception as e:
        return err(str(e))
