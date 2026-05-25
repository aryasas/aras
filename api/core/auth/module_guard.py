# claude-sonnet-4-6
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import Callable, Optional
import logging

from core.lib.database import get_db
from core.auth.service import get_current_user
from apps.saas.models import Plan

logger = logging.getLogger(__name__)


# claude-sonnet-4-6
def get_tenant_plan(db: Session, tenant_id: str) -> Optional[Plan]:
    from apps.saas.models import Subscription
    from sqlalchemy.orm import joinedload
    sub = db.query(Subscription).options(joinedload(Subscription.plan)).filter_by(tenant_id=tenant_id).first()
    return sub.plan if sub else None


# claude-sonnet-4-6
def require_module(module_name: str) -> Callable:
    def dependency(
        request: Request,
        db: Session = Depends(get_db),
        current_user=Depends(get_current_user),
    ) -> None:
        tenant_id = getattr(current_user, "tenant_id", None)
        if not tenant_id:
            from apps.saas.models import Subscription
            sub = db.query(Subscription).filter(
                Subscription.email == current_user.email,
                Subscription.status.in_(["active", "trial"]),
            ).first()
            tenant_id = sub.tenant_id if sub else None

        if not tenant_id:
            raise HTTPException(status_code=403, detail="No active subscription found.")

        if not hasattr(request.state, "tenant_plan"):
            plan = get_tenant_plan(db, tenant_id)
            if not plan:
                raise HTTPException(status_code=403, detail="Plan configuration not found.")
            request.state.tenant_plan = plan

        plan: Plan = request.state.tenant_plan
        active_modules = plan.active_modules or []

        if module_name not in active_modules:
            logger.warning("Tenant '%s' blocked from module '%s'", tenant_id, module_name)
            raise HTTPException(
                status_code=403,
                detail=f"Module '{module_name}' not available on your plan. Upgrade required.",
            )

    return dependency
