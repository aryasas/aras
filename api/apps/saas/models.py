from typing import Optional
from sqlalchemy import String, Integer, Boolean, JSON, ForeignKey, DateTime, text, func
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
    trial_days: Mapped[int] = mapped_column(Integer, default=14)
    annual_discount_pct: Mapped[int] = mapped_column(Integer, default=0)

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
    billing_cycle: Mapped[str] = mapped_column(String(20), default="monthly") # monthly, annual
    next_billing_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    default_provider_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    trial_ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    plan = relationship("Plan")

    # gemini-2-5-flash
    @Aras.model_action(name="approve", permission="edit", label="Approve & Provision", icon="UserCheck")
    def approve(self, db):
        """Approve pending signup: gate on payment, provision tenant, send email."""
        from core.response import err as aras_err
        
        if self.status not in ["pending", "pending_payment"]:
            return ok({}, message=f"Cannot approve: status is '{self.status}'.")

        # Check if there's a paid invoice
        latest_invoice = db.query(SaaSInvoice).filter_by(subscription_id=self.id).order_by(SaaSInvoice.id.desc()).first()
        
        # If no paid invoice exists for this subscription, require payment
        if latest_invoice and latest_invoice.status != "paid":
             return aras_err("Payment not confirmed")

        from .services.provisioner import Provisioner
        from .services.email import send_setup_email
        try:
            result = Provisioner.provision_tenant(db, self)
            self.tenant_id = result["tenant_id"]
            self.status = "active"
            self.started_at = datetime.now()
            
            # Send setup email
            send_setup_email(self.email, result["setup_token"], self.company_name)
            
            return ok(result, message=f"Approved and provisioned: {self.tenant_id}. Setup email sent.")
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Provisioning failed: {e}")
            return aras_err(f"Provisioning failed: {str(e)}")

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

# gemini-2-5-flash
class PaymentMethod(Aras.Model):
    __tablename__ = "saas_payment_method"
    code: Mapped[str] = mapped_column(String(50), unique=True)
    label: Mapped[str] = mapped_column(String(100))
    provider_code: Mapped[str] = mapped_column(String(50)) # stripe, midtrans, xendit
    country: Mapped[str] = mapped_column(String(10), default="*")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

# gemini-2-5-flash
class SaaSPayment(Aras.Model):
    __tablename__ = "saas_payment"
    subscription_id: Mapped[int] = mapped_column(ForeignKey("saas_subscription.id"))
    provider_code: Mapped[str] = mapped_column(String(50))
    provider_payment_id: Mapped[str] = mapped_column(String(255), index=True)
    amount: Mapped[int] = mapped_column(Integer) # in cents/units
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20)) # succeeded, failed, pending
    method_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    subscription = relationship("Subscription")

# gemini-2-5-flash
class SaaSInvoice(Aras.Model):
    __tablename__ = "saas_invoice"
    subscription_id: Mapped[int] = mapped_column(ForeignKey("saas_subscription.id"))
    number: Mapped[str] = mapped_column(String(50), unique=True)
    period_start: Mapped[datetime] = mapped_column(DateTime)
    period_end: Mapped[datetime] = mapped_column(DateTime)
    amount: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="unpaid") # unpaid, paid, void, overdue
    due_at: Mapped[datetime] = mapped_column(DateTime)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    payment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("saas_payment.id"), nullable=True)

    subscription = relationship("Subscription")
    payment = relationship("SaaSPayment")

# gemini-2-5-flash
class RequestLog(Aras.Model):
    __tablename__ = "aras_request_log"
    tenant_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    path: Mapped[str] = mapped_column(String(255))
    method: Mapped[str] = mapped_column(String(10))
    status: Mapped[int] = mapped_column(Integer)
    duration_ms: Mapped[int] = mapped_column(Integer)
    ts: Mapped[datetime] = mapped_column(DateTime, default=func.now())



