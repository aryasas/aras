import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure api/ is on the path when running pytest from the project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.lib.database import get_db
from core.base.model import Base
from main import app

# Disable bootstrap seeding during tests to avoid hangs/slowness
from core.manager import bootstrap
bootstrap.run = lambda db: None

# Disable Organization seeding hook
from sqlalchemy import event
from apps.config.models import Organization
from apps.config.models import _seed_reports_for_new_org
try:
    event.remove(Organization, "after_insert", _seed_reports_for_new_org)
except (ValueError, Exception):
    pass

# Use SQLite for local testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    return engine

@pytest.fixture(scope="function")
def db(db_engine):
    """Function-scoped database session with fresh schema per test."""
    Base.metadata.create_all(bind=db_engine)
    Session = sessionmaker(bind=db_engine)
    session = Session()

    yield session

    session.close()
    Base.metadata.drop_all(bind=db_engine)

@pytest.fixture(scope="function")
def client(db):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def admin_user(db):
    """Returns a test admin user."""
    from core.auth.models import User
    import uuid
    uid = str(uuid.uuid4())[:8]
    user = User(
        username=f"admin_{uid}",
        email=f"admin_{uid}@aras.local",
        password_hash=User.hash_password("password123"),
        is_admin=True
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def org(db):
    """Returns a test organization."""
    from apps.config.models import Organization
    import uuid
    uid = str(uuid.uuid4())[:8]
    org = Organization(name=f"Test Org {uid}", code=f"T{uid}")
    db.add(org)
    db.flush()
    db.refresh(org)
    return org

@pytest.fixture(scope="function")
def auth_headers():
    """Helper fixture to generate auth headers for a user."""
    from core.auth.service import create_access_token
    def _headers(user):
        token = create_access_token(data={"sub": user.username})
        return {"Authorization": f"Bearer {token}"}
    return _headers

@pytest.fixture(scope="function")
def auth_client(client, admin_user, auth_headers):
    """TestClient with auto-admin-token in headers."""
    client.headers.update(auth_headers(admin_user))
    return client
