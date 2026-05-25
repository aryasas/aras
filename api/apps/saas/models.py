from typing import Optional
from sqlalchemy import String, Integer, Boolean, JSON, ForeignKey, DateTime, text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core import Aras
from core.response import ok
from datetime import datetime, timedelta

# claude-sonnet-4-6
class Plan(Aras.Model):
    __tablename__ = "saas_plan"
    __field_hints__ = {
        "plan_key": {"help": "Lowercase slug, contoh: free, lite, growth"},
        "active_modules": {"help": "JSON list modul aktif, contoh: [\"pos\", \"stock\", \"accounting\"]"},
        "features": {"help": "JSON fitur tampilan, contoh: {\"included\": [\"...\", \"...\"]}"},
        "max_transactions": {"help": "-1 = unlimited"},
        "max_products": {"help": "-1 = unlimited"},
        "max_branches": {"help": "-1 = unlimited"},
        "max_users": {"help": "-1 = unlimited"},
        "storage_mb": {"help": "-1 = unlimited"},
    }
    plan_key: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, server_default="")
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="IDR")
    # -1 = unlimited
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    max_branches: Mapped[int] = mapped_column(Integer, default=1)
    max_transactions: Mapped[int] = mapped_column(Integer, default=50)
    max_products: Mapped[int] = mapped_column(Integer, default=30)
    storage_mb: Mapped[int] = mapped_column(Integer, default=256)
    active_modules: Mapped[list] = mapped_column(JSON, default=list, server_default=text("'[]'"))
    api_access: Mapped[bool] = mapped_column(Boolean, default=False)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# claude-opus-4-7
class Subscription(Aras.Model):
    __tablename__ = "saas_subscription"
    __admin_only__ = True
    # Signup-time fields (filled on /signup, before approval)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Tenant identity (assigned on approve)
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, unique=True)
    plan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("saas_plan.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", info={"choices": ["pending", "trial", "active", "suspended", "cancelled", "rejected"]})
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    plan = relationship("Plan")

    # claude-opus-4-7
    @Aras.model_action(name="approve", permission="edit", label="Approve & Provision", icon="UserCheck")
    def approve(self, db):
        """Approve pending signup: assign tenant_id, create User, start trial, issue setup link."""
        from core.lib.helpers import slugify
        from core.auth.models import User
        from core.auth.service import create_access_token
        import secrets

        if self.status != "pending":
            return ok({}, message=f"Cannot approve: status is '{self.status}'.")
        if not self.plan_id:
            return ok({}, message="Cannot approve: no plan selected.")

        slug = slugify(self.company_name)
        self.tenant_id = f"{slug}-{self.id}"
        now = datetime.now()
        self.started_at = now
        self.expires_at = now + timedelta(days=14)
        self.status = "trial"

        # Create User with random password — customer sets via setup link
        existing_user = db.query(User).filter_by(email=self.email).first()
        if not existing_user:
            random_pw = secrets.token_urlsafe(24)
            user = User(
                username=self.email,
                email=self.email,
                password_hash=User.hash_password(random_pw),
                is_active=True,
                is_admin=False,
            )
            db.add(user)

        # One-time setup token (1h) — customer clicks to set password
        setup_token = create_access_token(
            {"sub": self.email, "purpose": "portal_setup", "tenant": self.tenant_id},
            expires_delta=timedelta(hours=1),
        )
        setup_link = f"/portal/setup?token={setup_token}"

        # Issue trial license (14 days)
        from .services.license_service import LicenseService
        try:
            license_token = LicenseService.issue_license(db, self.id, expiry_days=14)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to issue license: {e}")
            license_token = None

        return ok(
            {"display_token": setup_link, "license_token": license_token},
            message=f"Approved. Send this setup link to {self.email} (expires in 1h). License issued.",
        )

    # claude-opus-4-7
    @Aras.model_action(name="reject", permission="edit", label="Reject", icon="X")
    def reject(self, db):
        if self.status != "pending":
            return ok({}, message=f"Cannot reject: status is '{self.status}'.")
        self.status = "rejected"
        return ok({}, message="Signup rejected.")

    @Aras.model_action(name="issue_license", permission="edit", label="Issue License", icon="Key")
    def issue_license(self, db):
        from .services.license_service import LicenseService
        token = LicenseService.issue_license(db, self.id, 30)
        return ok({"display_token": token}, message="License issued successfully.")

    @Aras.model_action(name="suspend", permission="edit", label="Suspend", icon="Ban")
    def suspend(self, db):
        from .services.license_service import LicenseService
        self.status = "suspended"
        token_obj = db.query(LicenseToken).filter_by(subscription_id=self.id, revoked=False).order_by(LicenseToken.issued_at.desc()).first()
        if token_obj:
            LicenseService.revoke_license(db, token_obj.id)
        return ok({}, message="Subscription suspended and license revoked.")

    @Aras.model_action(name="activate", permission="edit", label="Activate", icon="CheckCircle")
    def activate(self, db):
        from .services.license_service import LicenseService
        self.status = "active"
        token = LicenseService.issue_license(db, self.id, 30)
        return ok({"display_token": token}, message="Subscription activated.")

class LicenseToken(Aras.Model):
    __tablename__ = "saas_license_token"
    __admin_only__ = True
    subscription_id: Mapped[int] = mapped_column(ForeignKey("saas_subscription.id"))
    token: Mapped[str] = mapped_column(String(1000), nullable=False)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription = relationship("Subscription")

class ActivationRequest(Aras.Model):
    __tablename__ = "saas_activation_request"
    __admin_only__ = True
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    instance_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", info={"choices": ["pending", "approved", "rejected"]})
    requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

