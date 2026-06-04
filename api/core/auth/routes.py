from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..base.validation import Validation
from ..lib.database import get_db
from ..lib.settings import settings
from ..lib.config import ConfigService
from .service import (
    create_access_token, 
    get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_password_reset_token,
    verify_password_reset_token
)
from .models import User, UserPreference
from pydantic import BaseModel

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

class ChangePasswordRequest(Validation):
    old_password: str
    new_password: str

class ForgotPasswordRequest(Validation):
    email: str

class ResetPasswordRequest(Validation):
    token: str
    new_password: str

@router.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = User.authenticate(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user.username, "purpose": "access"},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
def read_users_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Plugin integration point: an app provides org list when installed.
    # Resolved by key so core never imports the app (core↛apps invariant).
    from core.service_registry import ServiceRegistry
    get_user_org_list = ServiceRegistry.get("get_user_org_list")
    companies = get_user_org_list(db, current_user) if get_user_org_list else []
    default_org = next((c for c in companies if c.get("is_default")), None)
    default_org_id = default_org["id"] if default_org else (companies[0]["id"] if companies else None)
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": current_user.name,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "organizations": companies,
        "default_org_id": default_org_id,
    }


class UpdateProfileRequest(Validation):
    name: str
    email: str


@router.put("/me")
def update_profile(
    data: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if data.email != current_user.email:
        existing = db.query(User).filter(User.email == data.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )
    
    current_user.name = data.name
    current_user.email = data.email
    db.commit()
    return {"message": "Profile updated successfully"}


@router.post("/change-password")
def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.verify_password(data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )

    min_len = int(ConfigService.get(db, "core.password_min_length") or 8)
    if len(data.new_password) < min_len:
        raise HTTPException(status_code=422, detail=f"Password must be at least {min_len} characters")
    if data.new_password == current_user.username:
        raise HTTPException(status_code=422, detail="Password cannot be the same as your username")

    current_user.password_hash = User.hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # We don't want to reveal if a user exists or not for security
        return {"message": "If an account with that email exists, we have sent a reset link."}
    
    token = create_password_reset_token(user.email)
    
    if settings.DEBUG:
        print(f"DEBUG: Password reset token for {user.email}: {token}")
    
    return {"message": "If an account with that email exists, we have sent a reset link."}

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    email = verify_password_reset_token(data.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    min_len = int(ConfigService.get(db, "core.password_min_length") or 8)
    if len(data.new_password) < min_len:
        raise HTTPException(status_code=422, detail=f"Password must be at least {min_len} characters")

    user.password_hash = User.hash_password(data.new_password)
    db.commit()
    return {"message": "Password has been reset successfully"}


class UserPreferenceBody(BaseModel):
    key: str
    value: str


# claude-sonnet-4-6
@router.get("/preference")
def get_user_preference(
    key: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == user.id,
        UserPreference.key == key
    ).first()
    return {"key": key, "value": pref.value if pref else None}


# claude-sonnet-4-6
@router.put("/preference")
def set_user_preference(
    body: UserPreferenceBody,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    pref = db.query(UserPreference).filter(
        UserPreference.user_id == user.id,
        UserPreference.key == body.key
    ).first()
    if pref:
        pref.value = body.value
    else:
        pref = UserPreference(user_id=user.id, key=body.key, value=body.value)
        db.add(pref)
    db.commit()
    return {"key": body.key, "value": body.value}
