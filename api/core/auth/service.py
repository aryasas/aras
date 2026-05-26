from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..lib.database import get_db
from ..lib.settings import settings
from .models import User

ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
PASSWORD_RESET_EXPIRE_MINUTES = settings.PASSWORD_RESET_EXPIRE_MINUTES

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def _parse_positive_int(value: Any, *, header_name: str) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {header_name} header")
    if parsed <= 0:
        raise HTTPException(status_code=400, detail=f"Invalid {header_name} header")
    return parsed


def user_can_access_org(db: Session, user: User, org_id: int) -> bool:
    """Return whether a user is allowed to operate in an organization context."""
    if user.is_admin:
        return True
    try:
        from apps.config.erp_rbac import get_access
    except ImportError:
        return False

    access = get_access(db, user.id)
    if access["scope"] == "ALL":
        return True
    return org_id in set(access.get("org_ids") or [])


def user_org_scope(db: Session, user: User) -> Optional[list[int]]:
    """Return allowed org IDs for scoped filtering; None means unrestricted."""
    if user.is_admin:
        return None
    try:
        from apps.config.erp_rbac import get_access
    except ImportError:
        return []

    access = get_access(db, user.id)
    if access["scope"] == "ALL":
        return None
    if access["scope"] == "SPECIFIC":
        return list(access.get("org_ids") or [])
    return []


def require_org_access(db: Session, user: User, org_id: int):
    if not user_can_access_org(db, user, org_id):
        raise HTTPException(status_code=403, detail="Organization access denied")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_password_reset_token(email: str):
    expire = datetime.now(timezone.utc) + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": email, "purpose": "password_reset"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("purpose") != "password_reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        purpose: str = payload.get("purpose")
        if username is None or purpose not in (None, "access"):
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception

    from ..logic.scope import ScopeContext
    raw: dict = {}
    scoped_org_id: Optional[int] = None
    for key, value in request.headers.items():
        if not key.lower().startswith("x-scope-"):
            continue
        parsed = _parse_positive_int(value, header_name=key)
        if parsed is not None:
            scope_key = key[8:].lower().replace("-", "_")
            if scope_key != "org_id":
                raise HTTPException(status_code=400, detail=f"Unsupported scope header: {key}")
            scoped_org_id = parsed

    oid = _parse_positive_int(request.headers.get("X-Org-ID"), header_name="X-Org-ID") or 0
    if scoped_org_id:
        if oid and oid != scoped_org_id:
            raise HTTPException(status_code=400, detail="Conflicting organization scope headers")
        oid = scoped_org_id

    if oid:
        require_org_access(db, user, oid)
        # Always strict: user sees only the selected org's data.
        # Consolidated view is handled by "All" (no X-Org-ID header).
        raw["org_id"] = oid
    else:
        allowed_org_ids = user_org_scope(db, user)
        if allowed_org_ids is not None:
            raw["org_id"] = allowed_org_ids
    request.state.scope = ScopeContext(raw)
    request.state.org_id = oid  # keep direct org_id for writes
    return user


def get_current_user_optional(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False))
) -> Optional[User]:
    """Returns the authenticated user if token is present and valid, otherwise None."""
    if not token:
        return None
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
        return db.query(User).filter(User.username == username).first()
    except JWTError:
        return None


def require_admin(user: Any = Depends(get_current_user)):
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Administrator access required")
    return user
