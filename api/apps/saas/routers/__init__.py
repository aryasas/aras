from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from core.base.validation import Validation
from core.lib.database import get_db
from core.lib.settings import settings
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from ..models import Subscription, Plan, LicenseToken
from core.auth.models import User
from ..services.license_service import LicenseService
from core.auth.license import verify_license_token
from core.auth.service import create_access_token, require_admin
from datetime import datetime, timedelta, timezone
from core.lib.limiter import limiter
from fastapi import Request

router = APIRouter(prefix="", tags=["SaaS Control Panel"])
PUBLIC_PLAN_KEYS = ("free", "lite", "growth", "business", "enterprise")

class AdminUpdatePlanRequest(Validation):
    plan_id: int

class SignupRequest(Validation):
    email: str
    company_name: str
    full_name: str
    phone: Optional[str] = None
    plan_id: Optional[int] = None
    marketing_consent: bool = False

class ConsumerRegisterRequest(SignupRequest):
    password: str

class PortalLoginRequest(Validation):
    email: str
    password: str

class PortalSetupRequest(Validation):
    token: str
    new_password: str

class PortalSubscribeRequest(Validation):
    plan_id: int

class PortalPaymentRequest(Validation):
    provider: str = "dev"
    reference: Optional[str] = None


def _portal_token(email: str, tenant_id: str) -> str:
    return create_access_token(
        {"sub": tenant_id, "email": email, "purpose": "portal"},
        expires_delta=timedelta(hours=1),
    )


def _decode_portal_authorization(authorization: str) -> dict[str, Any]:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ", 1)[1]
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if payload.get("purpose") != "portal":
        raise HTTPException(status_code=401, detail="Invalid portal token")
    return payload


def _get_portal_subscription(db: Session, authorization: str) -> Subscription:
    payload = _decode_portal_authorization(authorization)
    tenant_id = payload.get("sub")
    sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return sub

# gemini-flash
@router.get("/tenant-config")
def get_tenant_config(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.split(" ", 1)[1]
    payload = verify_license_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired license token")
    
    # Verify token is not revoked in DB
    token_rec = db.query(LicenseToken).filter_by(token=token).first()
    if not token_rec or token_rec.revoked:
        raise HTTPException(status_code=403, detail="License token has been revoked")

    tenant_id = payload.get("sub")
    sub = db.query(Subscription).options(joinedload(Subscription.plan)).filter_by(tenant_id=tenant_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")

    if sub.status not in ("active", "trial"):
        raise HTTPException(status_code=403, detail=f"Subscription is {sub.status}")

    plan = sub.plan
    if not plan:
        raise HTTPException(status_code=400, detail="No plan associated with subscription")
        
    return {
        "tenant_id": sub.tenant_id,
        "plan_key": plan.plan_key,
        "active_modules": plan.active_modules,
        "max_users": plan.max_users,
        "max_branches": plan.max_branches,
        "max_transactions": plan.max_transactions,
        "max_products": plan.max_products,
        "storage_mb": plan.storage_mb,
        "api_access": plan.api_access,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None
    }


# gpt-5
@router.post("/signup")
@limiter.limit("5/minute")
def signup(request: Request, data: SignupRequest, db: Session = Depends(get_db)):
    consent_at = datetime.now(timezone.utc) if data.marketing_consent else None
    existing = db.query(Subscription).filter_by(email=data.email).first()
    if existing:
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": "Email already registered."}
        )
    sub = Subscription(
        email=data.email,
        company_name=data.company_name,
        full_name=data.full_name,
        phone=data.phone,
        plan_id=data.plan_id,
        marketing_consent=data.marketing_consent,
        consent_at=consent_at,
        status="pending",
        auto_renew=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"success": True, "subscription_id": sub.id}


@router.post("/portal/register")
# gpt-5
@limiter.limit("5/minute")
def portal_register(request: Request, data: ConsumerRegisterRequest, db: Session = Depends(get_db)):
    """Self-service consumer registration. Payment/activation happens separately."""
    from core.lib.helpers import slugify

    consent_at = datetime.now(timezone.utc) if data.marketing_consent else None
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    if db.query(User).filter_by(email=data.email).first() or db.query(Subscription).filter_by(email=data.email).first():
        return JSONResponse(
            status_code=409,
            content={"success": False, "error": "Email already registered."}
        )

    user = User(
        username=data.email,
        email=data.email,
        password_hash=User.hash_password(data.password),
        is_active=True,
        is_admin=False,
        marketing_consent=data.marketing_consent,
        consent_at=consent_at,
    )
    db.add(user)
    sub = Subscription(
        email=data.email,
        company_name=data.company_name,
        full_name=data.full_name,
        phone=data.phone,
        plan_id=data.plan_id,
        marketing_consent=data.marketing_consent,
        consent_at=consent_at,
        status="pending",
        auto_renew=True,
    )
    db.add(sub)
    db.flush()
    tenant_id = f"{slugify(data.company_name)}-{sub.id}"
    sub.tenant_id = tenant_id
    db.commit()
    return {
        "success": True,
        "subscription_id": sub.id,
        "tenant_id": tenant_id,
        "token": _portal_token(data.email, tenant_id),
    }


@router.post("/portal/subscribe")
def portal_subscribe(
    data: PortalSubscribeRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    sub = _get_portal_subscription(db, authorization)
    plan = db.query(Plan).filter_by(id=data.plan_id, is_active=True).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if sub.status not in ("pending", "trial", "active"):
        raise HTTPException(status_code=400, detail=f"Cannot subscribe while subscription is {sub.status}")

    sub.plan_id = plan.id
    if sub.status == "active":
        sub.status = "pending"
    db.commit()
    return {
        "success": True,
        "subscription_id": sub.id,
        "status": sub.status,
        "plan": _plan_payload(plan),
    }


@router.post("/portal/payment/dev-bypass")
def portal_payment_dev_bypass(
    data: PortalPaymentRequest,
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    if not (settings.DEBUG or settings.TESTING):
        raise HTTPException(status_code=403, detail="Development payment bypass is disabled")

    sub = _get_portal_subscription(db, authorization)
    if not sub.plan_id:
        raise HTTPException(status_code=400, detail="Select a plan before payment")
    if sub.status not in ("pending", "trial", "active"):
        raise HTTPException(status_code=400, detail=f"Cannot activate subscription in status {sub.status}")

    now = datetime.now(timezone.utc)
    sub.status = "active"
    sub.started_at = sub.started_at or now
    sub.expires_at = now + timedelta(days=30)
    token = LicenseService.issue_license(db, sub.id, 30)
    db.commit()
    return {
        "success": True,
        "status": sub.status,
        "subscription_id": sub.id,
        "tenant_id": sub.tenant_id,
        "license_token": token,
        "payment": {
            "provider": data.provider,
            "reference": data.reference or f"dev-{sub.id}",
            "bypassed": True,
        },
    }


# gemini-flash
@router.get("/plans/public")
def get_plans_public(db: Session = Depends(get_db)):
    plans = (
        db.query(Plan)
        .filter(Plan.is_active == True, Plan.plan_key.in_(PUBLIC_PLAN_KEYS))  # noqa: E712
        .order_by(Plan.sort_order, Plan.price)
        .all()
    )
    return [_plan_payload(p) for p in plans]


# claude-sonnet-4-6
def _plan_payload(plan: Plan) -> dict[str, Any]:
    features = dict(plan.features or {})
    if "apps" not in features:
        plan_name = (plan.name or "").lower()
        plan_key = (getattr(plan, "plan_key", "") or "").lower()
        modules = set(getattr(plan, "active_modules", []) or [])
        if plan_name == "starter" or plan_key == "starter":
            features["apps"] = ["accounting", "party", "report"]
        elif plan_name == "business" or plan_key == "business":
            features["apps"] = ["accounting", "party", "report", "stock", "pot"]
        elif plan_name == "enterprise" or plan_key == "enterprise":
            features["apps"] = ["accounting", "party", "report", "stock", "pot", "crm", "hr", "asset"]
        else:
            module_apps = {
                "accounting": "accounting",
                "stock": "stock",
                "pos": "pot",
                "receivable": "accounting",
                "crm": "crm",
                "hr": "hr",
                "asset": "asset",
                "ticket": "ticket",
                "web": "web",
            }
            apps = ["party", "report", "notes"]
            for module in modules:
                app_name = module_apps.get(module)
                if app_name and app_name not in apps:
                    apps.append(app_name)
            features["apps"] = apps

    return {
        "id": plan.id,
        "plan_key": getattr(plan, "plan_key", None),
        "name": plan.name,
        "price": plan.price,
        "currency": plan.currency,
        "max_users": plan.max_users,
        "max_branches": plan.max_branches,
        "max_transactions": getattr(plan, "max_transactions", 50),
        "max_products": getattr(plan, "max_products", 30),
        "storage_mb": getattr(plan, "storage_mb", 256),
        "active_modules": getattr(plan, "active_modules", []),
        "api_access": getattr(plan, "api_access", False),
        "sort_order": getattr(plan, "sort_order", 0),
        "features": features,
    }


# claude-opus-4-7
@router.post("/portal/login")
@limiter.limit("5/minute")
def portal_login(request: Request, data: PortalLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not user.verify_password(data.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    sub = db.query(Subscription).filter(
        Subscription.email == data.email,
        Subscription.status.in_(["trial", "active"]),
    ).first()
    if not sub or not sub.tenant_id:
        raise HTTPException(status_code=401, detail="No active subscription for this account")
    token = create_access_token(
        {"sub": sub.tenant_id, "email": data.email, "purpose": "portal"},
        expires_delta=timedelta(hours=1),
    )
    return {"success": True, "token": token, "tenant_id": sub.tenant_id, "expires_in": 3600}


# claude-opus-4-7
@router.post("/portal/setup")
@limiter.limit("5/minute")
def portal_setup(request: Request, data: PortalSetupRequest, db: Session = Depends(get_db)):
    """Customer clicks setup link from admin's approval message → sets their real password."""
    from core.lib.settings import settings
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(data.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired setup link")
    if payload.get("purpose") != "portal_setup":
        raise HTTPException(status_code=401, detail="Invalid setup link")
    email = payload.get("sub")
    user = db.query(User).filter_by(email=email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Account not found")
    if len(data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    user.password_hash = User.hash_password(data.new_password)
    db.commit()
    return {"success": True, "message": "Password set. You can now sign in to the portal."}


# gemini-flash
@router.get("/portal/subscription")
def get_portal_subscription(
    db: Session = Depends(get_db),
    authorization: str = Header(...)
):
    sub = _get_portal_subscription(db, authorization)
        
    latest_token = db.query(LicenseToken).filter_by(subscription_id=sub.id, revoked=False).order_by(desc(LicenseToken.issued_at)).first()
    
    return {
        "tenant_id": sub.tenant_id,
        "plan": _plan_payload(sub.plan) if sub.plan else None,
        "status": sub.status,
        "started_at": sub.started_at,
        "expires_at": sub.expires_at,
        "auto_renew": sub.auto_renew,
        "latest_token": {
            "token": latest_token.token,
            "expires_at": latest_token.expires_at,
            "revoked": latest_token.revoked
        } if latest_token else None
    }


@router.get("/portal/apps")
def get_portal_apps(
    db: Session = Depends(get_db),
    authorization: str = Header(...),
):
    sub = _get_portal_subscription(db, authorization)
    if sub.status not in ("trial", "active"):
        raise HTTPException(status_code=402, detail="Subscription payment required")
    if not sub.plan:
        raise HTTPException(status_code=400, detail="Subscription has no plan")

    from core.base.app import App
    plan_payload = _plan_payload(sub.plan)
    features = plan_payload["features"]
    allowed = features.get("apps", [])
    allow_all = allowed == "*" or allowed == ["*"]
    if isinstance(allowed, str):
        allowed = [allowed]

    apps = []
    for app_cls in App._registry.values():
        if app_cls.app_name in {"admin", "saas"}:
            continue
        if not allow_all and app_cls.app_name not in allowed:
            continue
        apps.append({
            "name": app_cls.app_name,
            "label": app_cls.app_label,
            "icon": app_cls.icon,
            "path": app_cls._get_clean_path(),
            "have_home": app_cls.have_home,
        })

    return {
        "tenant_id": sub.tenant_id,
        "plan": plan_payload,
        "apps": apps,
        "features": features,
        "limits": {
            "max_users": sub.plan.max_users,
            "max_branches": sub.plan.max_branches,
        },
    }


# gemini
@router.get("/admin/subscriptions")
def admin_list_subscriptions(
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """List all subscriptions (admin only)."""
    subs = db.query(Subscription).options(joinedload(Subscription.plan)).order_by(desc(Subscription.id)).all()
    return [{
        "id": s.id,
        "tenant_id": s.tenant_id,
        "status": s.status,
        "plan_key": s.plan.plan_key if s.plan else None,
        "email": s.email,
        "created_at": s.created_at
    } for s in subs]


# gemini
@router.post("/admin/subscriptions/{id}/approve")
def admin_approve_subscription(
    id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Approve a subscription and trigger provisioning."""
    sub = db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    res = sub.approve(db)
    db.commit()
    return res


# gemini
@router.post("/admin/subscriptions/{id}/suspend")
def admin_suspend_subscription(
    id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Suspend an active subscription and revoke license."""
    sub = db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    res = sub.suspend(db)
    db.commit()
    return res


# gemini
@router.patch("/admin/subscriptions/{id}/plan")
def admin_update_subscription_plan(
    id: int,
    data: AdminUpdatePlanRequest,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Update subscription plan."""
    sub = db.get(Subscription, id)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    sub.plan_id = data.plan_id
    db.commit()
    return {"success": True}


# gemini
@router.get("/admin/subscriptions/{id}")
def admin_get_subscription(
    id: int,
    db: Session = Depends(get_db),
    _: Any = Depends(require_admin)
):
    """Get detailed subscription info with latest license status."""
    sub = db.query(Subscription).options(joinedload(Subscription.plan)).filter_by(id=id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    latest_token = db.query(LicenseToken).filter_by(subscription_id=sub.id).order_by(desc(LicenseToken.issued_at)).first()
    
    return {
        "id": sub.id,
        "email": sub.email,
        "company_name": sub.company_name,
        "full_name": sub.full_name,
        "phone": sub.phone,
        "tenant_id": sub.tenant_id,
        "status": sub.status,
        "started_at": sub.started_at,
        "expires_at": sub.expires_at,
        "auto_renew": sub.auto_renew,
        "notes": sub.notes,
        "plan": _plan_payload(sub.plan) if sub.plan else None,
        "latest_license": {
            "token": latest_token.token if latest_token else None,
            "issued_at": latest_token.issued_at if latest_token else None,
            "expires_at": latest_token.expires_at if latest_token else None,
            "revoked": latest_token.revoked if latest_token else None
        }
    }
