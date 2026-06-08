import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey, select, update, Index
from .models import User
from core.base.model import Model

# gemini-3-flash-preview
class RefreshToken(Model):
    __tablename__ = "core_refresh_tokens"
    __table_args__ = (
        {"extend_existing": True}
    )

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("core_users.id"))
    token_hash: Mapped[str] = mapped_column(String(256))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    replaced_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # ID of the new token

# gemini-3-flash-preview
def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

# gemini-3-flash-preview
def create_refresh_token(db: Session, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at
    )
    db.add(refresh_token)
    db.commit()
    return token

# gemini-3-flash-preview
def rotate_refresh_token(db: Session, token: str) -> Optional[Tuple[str, int]]:
    token_hash = hash_token(token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    rt = db.scalar(stmt)

    if not rt:
        return None

    # Detect reuse of a revoked token -> revoke whole chain
    if rt.revoked_at:
        revoke_token_chain(db, rt.user_id)
        return None

    expires_at = rt.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at < datetime.now(timezone.utc):
        return None

    # Revoke current
    rt.revoked_at = datetime.now(timezone.utc)
    
    # Issue new
    new_token = secrets.token_urlsafe(32)
    new_token_hash = hash_token(new_token)
    new_expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    new_rt = RefreshToken(
        user_id=rt.user_id,
        token_hash=new_token_hash,
        expires_at=new_expires_at
    )
    db.add(new_rt)
    db.flush() # Get ID
    
    rt.replaced_by = new_rt.id
    db.commit()
    
    return new_token, rt.user_id

# gemini-3-flash-preview
def revoke_token_chain(db: Session, user_id: int):
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id)
        .where(RefreshToken.revoked_at == None)
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.execute(stmt)
    db.commit()

# gemini-3-flash-preview
def revoke_refresh_token(db: Session, token: str):
    token_hash = hash_token(token)
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked_at=datetime.now(timezone.utc))
    )
    db.execute(stmt)
    db.commit()
