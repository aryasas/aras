# gemini-2-5-flash
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from core.lib.database import get_db
from core.response import ok, err
from core.auth.service import require_admin
from ..models import Subscription, SaaSPayment
from ..services.metrics import MetricsService
from sqlalchemy import func

router = APIRouter(prefix="/admin", tags=["SaaS Admin"])

@router.get("/tenants")
async def list_tenants(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    tenants = db.query(Subscription).filter(Subscription.tenant_id.isnot(None)).all()
    return ok(tenants)

@router.get("/tenants/{tenant_id}/metrics")
async def get_tenant_metrics(tenant_id: str, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    metrics = MetricsService.tenant_usage(db, tenant_id)
    return ok(metrics)

@router.get("/revenue")
async def get_revenue(db: Session = Depends(get_db), current_user = Depends(require_admin)):
    # Simple MRR calculation based on active subscriptions
    mrr = db.query(func.sum(SaaSPayment.amount)).filter(SaaSPayment.status == "succeeded").scalar() or 0
    return ok({
        "mrr": mrr,
        "arr": mrr * 12,
        "churn": 0,
        "active_tenants": db.query(func.count(Subscription.id)).filter(Subscription.status == "active").scalar()
    })
