from typing import Optional
from sqlalchemy import String, Integer, Boolean, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Mapped, mapped_column
from core import Aras
from core.response import ok
from datetime import datetime

class Plan(Aras.Model):
    __tablename__ = "saas_plan"
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[int] = mapped_column(Integer, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    max_users: Mapped[int] = mapped_column(Integer, default=1)
    max_branches: Mapped[int] = mapped_column(Integer, default=1)
    features: Mapped[dict] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

class Subscription(Aras.Model):
    __tablename__ = "saas_subscription"
    tenant_id: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("saas_plan.id"))
    status: Mapped[str] = mapped_column(String(20), default="trial", info={"choices": ["trial", "active", "suspended", "cancelled"]})
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    auto_renew: Mapped[bool] = mapped_column(Boolean, default=True)

    plan = relationship("Plan")

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
    subscription_id: Mapped[int] = mapped_column(ForeignKey("saas_subscription.id"))
    token: Mapped[str] = mapped_column(String(1000), nullable=False)
    issued_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    subscription = relationship("Subscription")

class ActivationRequest(Aras.Model):
    __tablename__ = "saas_activation_request"
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    instance_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", info={"choices": ["pending", "approved", "rejected"]})
    requested_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
