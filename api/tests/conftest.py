import pytest
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.lib.database import get_db
from core.base.model import Base
from core.lib.settings import settings
from main import app

# Use SQLite for local testing, Postgres in CI if DATABASE_URL is set
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

@pytest.fixture(scope="session")
def db_engine():
    """Session-scoped database engine."""
    engine_args = {}
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
        engine_args["connect_args"] = {"check_same_thread": False}
        engine_args["poolclass"] = StaticPool

    engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_args)
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db(db_engine):
    """Function-scoped transactional database session."""
    connection = db_engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

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
    user = User(
        username="admin_test",
        email="admin_test@aras.local",
        password_hash=User.hash_password("password123"),
        is_admin=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture(scope="function")
def org(db):
    """Returns a test organization."""
    from apps.config.models import Organization
    org = Organization(name="Test Org", code="TORG")
    db.add(org)
    db.commit()
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
