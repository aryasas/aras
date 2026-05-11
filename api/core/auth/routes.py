from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from ..aras import Aras
from ..lib.database import get_db
from .service import (
    create_access_token, 
    get_current_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_password_reset_token,
    verify_password_reset_token
)
from .models import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

class ChangePasswordRequest(Aras.Validation):
    old_password: str
    new_password: str

class ForgotPasswordRequest(Aras.Validation):
    email: str

class ResetPasswordRequest(Aras.Validation):
    token: str
    new_password: str

@router.post("/token")
async def login_for_access_token(
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
        data={"sub": user.username}, 
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin
    }

@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.verify_password(data.old_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    current_user.password_hash = User.hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}

@router.post("/forgot-password")
async def forgot_password(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        # We don't want to reveal if a user exists or not for security
        return {"message": "If an account with that email exists, we have sent a reset link."}
    
    token = create_password_reset_token(user.email)
    
    # In a real app, send email here. 
    # For this framework demo, we'll just log it or return it in a real-world "debug" way 
    # but for now let's just pretend we sent it.
    print(f"DEBUG: Password reset token for {user.email}: {token}")
    
    return {"message": "If an account with that email exists, we have sent a reset link."}

@router.post("/reset-password")
async def reset_password(
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
    
    user.password_hash = User.hash_password(data.new_password)
    db.commit()
    return {"message": "Password has been reset successfully"}
