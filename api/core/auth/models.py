from sqlalchemy.orm import Mapped
from sqlalchemy import String, Boolean, Integer, UniqueConstraint
from ..base.model import Model
from ..base.field import Field
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Model):
    __tablename__ = "auth_users"
    __admin_only__ = True

    username: Mapped[str] = Field(String(64), unique=True, index=True, label="Username")
    name: Mapped[str] = Field(String(100), nullable=True, label="Full Name")
    email: Mapped[str] = Field(String(120), unique=True, index=True, label="Email", ui_type="email")
    password_hash: Mapped[str] = Field(String(256), hidden=True, label="Password")
    is_active: Mapped[bool] = Field(Boolean, default=True, label="Is Active")
    is_admin: Mapped[bool] = Field(Boolean, default=False, label="Is Administrator")

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

    def __repr__(self):
        return f"<User {self.username}>"


# claude-sonnet-4-6
class UserPreference(Model):
    __tablename__ = "auth_user_preferences"
    __table_args__ = (UniqueConstraint("user_id", "key", name="uq_user_pref"),)

    user_id: Mapped[int] = Field(Integer, index=True, label="User")
    key: Mapped[str] = Field(String(128), label="Key")
    value: Mapped[str] = Field(String(4096), default="", label="Value")
