import logging
from typing import Dict, Generator, Optional
from fastapi import Request, HTTPException, Depends, status
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from threading import RLock

import os
from jose import jwt as pyjwt, JWTError

from .registry import tenant_registry

logger = logging.getLogger(__name__)

# A thread-safe cache for SQLAlchemy engines
_engine_cache: Dict[str, Engine] = {}
_engine_cache_lock = RLock()


def resolve_db_url(tenant_id: str) -> Optional[str]:
    """
    Resolves the database connection URL for a given tenant ID.

    Args:
        tenant_id: The ID of the tenant.

    Returns:
        The database URL as a string, or None if the tenant is not found.
    """
    tenant_info = tenant_registry.get(tenant_id)
    return tenant_info.get("db_url") if tenant_info else None


def get_or_create_engine(db_url: str) -> Engine:
    """
    Retrieves a SQLAlchemy engine from the cache or creates a new one.

    This function caches engines based on the database URL to avoid the overhead
    of creating new engines for every request.

    Args:
        db_url: The database URL for which to get or create an engine.

    Returns:
        A SQLAlchemy Engine instance.
    """
    with _engine_cache_lock:
        if db_url not in _engine_cache:
            logger.info(f"Creating new SQLAlchemy engine for URL (ending in): ...{db_url[-20:]}")
            try:
                engine = create_engine(db_url, pool_size=2, max_overflow=3)
                _engine_cache[db_url] = engine
            except Exception as e:
                logger.error(f"Failed to create engine for URL {db_url}: {e}")
                raise
        return _engine_cache[db_url]


def get_tenant_db(tenant_id: str) -> Optional[Session]:
    """
    Provides a SQLAlchemy session for a specific tenant.

    Args:
        tenant_id: The ID of the tenant.

    Returns:
        A SQLAlchemy Session, or None if the tenant cannot be resolved.
    """
    db_url = resolve_db_url(tenant_id)
    if not db_url:
        logger.warning(f"Failed to resolve DB URL for tenant_id: {tenant_id}")
        return None

    engine = get_or_create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def get_current_tenant(request: Request) -> str:
    """
    FastAPI dependency to extract the tenant ID from the request.

    Priority:
    1. TENANT_ID environment variable (for dedicated containers)
    2. 'X-Tenant-ID' header (for development/testing)
    3. 'sub' field of a JWT token

    Raises:
        HTTPException: If the tenant ID cannot be determined.

    Returns:
        The tenant ID as a string.
    """
    # 0. Check for environment variable first (gemini-pro)
    env_tenant_id = os.getenv("TENANT_ID")
    if env_tenant_id:
        return env_tenant_id

    # 1. Check for development header
    tenant_id = request.headers.get("x-tenant-id")
    if tenant_id:
        return tenant_id

    # 2. Fallback to JWT 'sub' field
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            secret = os.getenv("SECRET_KEY", "")
            payload = pyjwt.decode(token, secret, algorithms=["HS256"])
            tenant_id = payload.get("sub")
            if tenant_id:
                return tenant_id
        except (JWTError, Exception) as e:
            logger.debug("Could not extract tenant from JWT: %s", e)


    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not identify tenant. Missing X-Tenant-ID header or valid JWT.",
    )


def get_db(
    tenant_id: str = Depends(get_current_tenant),
) -> Generator[Session, None, None]:
    """
    FastAPI dependency to provide a transactional database session per request
    for the identified tenant.

    Args:
        tenant_id: The tenant ID, injected by the `get_current_tenant` dependency.

    Yields:
        A SQLAlchemy Session object.
    """
    db_url = resolve_db_url(tenant_id)
    if not db_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found or is not configured.",
        )

    engine = get_or_create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db: Optional[Session] = None
    try:
        db = SessionLocal()
        yield db
    finally:
        if db:
            db.close()
