import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .settings import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    # gemini-pro: dynamic tenant routing for dedicated containers
    tenant_id = os.getenv("TENANT_ID")
    if tenant_id:
        from core.tenant.router import resolve_db_url, get_or_create_engine
        db_url = resolve_db_url(tenant_id)
        if db_url:
            t_engine = get_or_create_engine(db_url)
            T_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=t_engine)
            db = T_SessionLocal()
            try:
                yield db
            finally:
                db.close()
            return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
