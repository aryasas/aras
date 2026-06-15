from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, UniqueConstraint, DateTime
from ..base.aras import Aras
from core.response import ok
from ..base.model import Model
from ..base.field import Field
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# gpt-5
class User(Model):
    __tablename__ = "core_users"
    __admin_only__ = True

    username: Mapped[str] = Field(String(64), unique=True, index=True, label="Username")
    name: Mapped[str] = Field(String(100), nullable=True, label="Full Name", pii=True)
    email: Mapped[str] = Field(String(120), unique=True, index=True, label="Email", ui_type="email", pii=True)
    password_hash: Mapped[str] = Field(String(256), hidden=True, label="Password")
    is_active: Mapped[bool] = Field(Boolean, default=True, label="Is Active")
    is_admin: Mapped[bool] = Field(Boolean, default=False, label="Is Administrator")
    # gemini-flash
    is_super_admin: Mapped[bool] = Field(Boolean, default=False, label="Is Super Administrator")
    marketing_consent: Mapped[bool] = Field(Boolean, default=False, label="Marketing Consent")
    consent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # gemini-3-flash-preview
    consent_version: Mapped[Optional[str]] = Field(String(32), nullable=True, label="Consent Version")
    # gemini-3-flash-preview
    consent_text_hash: Mapped[Optional[str]] = Field(String(64), nullable=True, label="Consent Text Hash")

    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.password_hash)

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @classmethod
    def authenticate(cls, db, username, password):
        user = db.query(cls).filter(cls.username == username).first()
        if not user or not user.verify_password(password):
            return None
        return user

    # gpt-5
    @Aras.model_action(name="anonymize", permission="delete", label="Anonymize")
    def anonymize(self, db):
        self.anonymize_self(db, user_id=self.id)
        return ok({"erased": True}, message="User anonymized.")

    def __repr__(self):
        return f"<User {self.username}>"


# claude-sonnet-4-6
class UserPreference(Model):
    __tablename__ = "core_user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_pref"),)

    user_id: Mapped[int] = Field(Integer, index=True, label="User")
    key: Mapped[str] = Field(String(128), label="Key")
    value: Mapped[str] = Field(String(4096), default="", label="Value")
