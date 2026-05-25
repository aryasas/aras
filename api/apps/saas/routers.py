from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from core.base.validation import Validation
from core.lib.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import desc
from .models import Subscription, Plan, LicenseToken
from core.auth.models import User
from .services.license_service import LicenseService
from core.auth.license import verify_license_token
from core.auth.service import create_access_token
from datetime import timedelta

router = APIRouter(prefix="", tags=["SaaS Control Plane"])

class RenewLicenseRequest(Validation):
    tenant_id: str
    current_token: str

class SignupRequest(Validation):
    email: str
    company_name: str
    full_name: str
    phone: Optional[str] = None
    plan_id: Optional[int] = None

class PortalLoginRequest(Validation):
    email: str
    password: str

class PortalSetupRequest(Validation):
    token: str
    new_password: str

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


# claude-opus-4-7
@router.post("/signup")
async def signup(data: SignupRequest, db: Session = Depends(get_db)):
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
        status="pending",
        auto_renew=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return {"success": True, "subscription_id": sub.id}


# gemini-flash
@router.get("/plans/public")
async def get_plans_public(db: Session = Depends(get_db)):
    plans = db.query(Plan).filter_by(is_active=True).order_by(Plan.price).all()
    return [{
        "id": p.id,
        "name": p.name,
        "price": p.price,
        "currency": p.currency,
        "max_users": p.max_users,
        "max_branches": p.max_branches,
        "features": p.features
    } for p in plans]


# claude-opus-4-7
@router.post("/portal/login")
async def portal_login(data: PortalLoginRequest, db: Session = Depends(get_db)):
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
async def portal_setup(data: PortalSetupRequest, db: Session = Depends(get_db)):
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
async def get_portal_subscription(
    db: Session = Depends(get_db),
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.split(" ")[1]
    
    from core.lib.settings import settings
    from jose import jwt, JWTError
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        tenant_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    sub = db.query(Subscription).filter_by(tenant_id=tenant_id).first()
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
        
    latest_token = db.query(LicenseToken).filter_by(subscription_id=sub.id, revoked=False).order_by(desc(LicenseToken.issued_at)).first()
    
    return {
        "tenant_id": tenant_id,
        "plan": {
            "id": sub.plan.id,
            "name": sub.plan.name,
            "price": sub.plan.price,
            "currency": sub.plan.currency
        },
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
