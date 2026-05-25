"""
Purpose: End-to-end verification of the Aras Framework core features.
Context: Runs against an isolated SQLite database via a dedicated engine.
Impact: Confirms Sync, Audit, Workflow, and Query logic.
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "api"))

from sqlalchemy import create_engine, event as sa_event
from sqlalchemy.orm import sessionmaker


@pytest.fixture(scope="function")
def db_session(tmp_path):
    db_url = f"sqlite:///{tmp_path}/test_framework.db"
    from core import Aras
    import os
    
    # Ensure all apps are discovered so models are registered
    Aras.discover_apps("apps")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Aras.Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    engine.dispose()


def _make_test_model():
    """Synthetic minimal model used in lieu of the removed apps.erp.Product toy."""
    from sqlalchemy import String, Float
    from sqlalchemy.orm import Mapped, mapped_column
    from core.base.model import Model

    if "test_framework_products" in Model._registry:
        return Model._registry["test_framework_products"]

    class _TestProduct(Model):
        __tablename__ = "test_framework_products"
        name: Mapped[str] = mapped_column(String(100))
        sku: Mapped[str] = mapped_column(String(50))
        price: Mapped[float] = mapped_column(Float, default=0)
        status: Mapped[str] = mapped_column(String(20), default="Draft")

    return _TestProduct


def test_sync_populates_registry(db_session):
    from core import Aras
    import os
    
    # Ensure all apps are discovered so models are registered
    Aras.discover_apps("apps")

    Aras.Manager.Sync.sync_all(db_session)

    app_count = db_session.query(Aras.AppModel).count()
    res_count = db_session.query(Aras.ResourceModel).count()
    assert app_count >= 2, f"Expected ≥2 apps synced, got {app_count}"
    assert res_count >= 5, f"Expected ≥5 resources synced, got {res_count}"


def test_workflow_transition(db_session):
    from core import Aras
    from core.auth.models import User

    Product = _make_test_model()
    Aras.Base.metadata.create_all(bind=db_session.get_bind())

    product = Product(name="WF Test", sku="WF001", price=10.0)
    product.__class__.__transitions__ = [
        {"name": "submit", "from": "Draft", "to": "Submitted", "permission": None}
    ]
    product.status = "Draft"
    db_session.add(product)
    db_session.commit()

    mock_user = User(username="test_admin", is_admin=True)
    success = Aras.Manager.Workflow.trigger_action(
        db_session, product, "submit", user=mock_user
    )
    assert success, "Workflow trigger_action returned False"
    assert product.status == "Submitted"


def test_query_builder_filters(db_session):
    from core.lib.query_builder import QueryBuilder
    from core import Aras

    Product = _make_test_model()
    Aras.Base.metadata.create_all(bind=db_session.get_bind())

    db_session.add(Product(name="Cheap", sku="C001", price=10.0))
    db_session.add(Product(name="Expensive", sku="E001", price=200.0))
    db_session.commit()

    results = QueryBuilder.execute(db_session, Product, [{"field": "price", "op": ">", "value": 50}])
    assert len(results) == 1
    assert results[0].name == "Expensive"
