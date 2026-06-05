import pytest


@pytest.fixture(autouse=True)
def stock_config_registry():
    from apps.stock.config_models import StockConfig
    from core.config import AppConfigRegistry

    AppConfigRegistry.register("stock", StockConfig)


@pytest.fixture
def stock_uom(db):
    from plugins.commerce.models import Uom

    uom = Uom(name="pcs")
    db.add(uom)
    db.flush()
    return uom


@pytest.fixture
def alert_org(db):
    from core.workspace.models import Organization

    org = Organization(name="Ops Org", code="OPS-ORG", email="ops@example.com")
    db.add(org)
    db.flush()
    return org


# gpt-5
def _posted_receipt(db, org_id: int, item_id: int, uom_id: int, location_id: int, qty: float):
    from apps.stock.models import StockMovement, StockMovementLine

    movement = StockMovement(org_id=org_id, number=f"SM-{item_id}-{qty}", move_type="receipt", status="Posted")
    db.add(movement)
    db.flush()
    db.add(
        StockMovementLine(
            movement_id=movement.id,
            item_id=item_id,
            qty=qty,
            uom_id=uom_id,
            qty_remaining=qty,
            to_location_id=location_id,
        )
    )
    db.flush()


# gpt-5
def test_low_stock_digest_sends_only_below_threshold(db, alert_org, stock_uom, monkeypatch):
    from apps.stock import jobs
    from apps.stock.models import Item, ItemLocation, Location
    from core.lib.config import ConfigService

    location = Location(org_id=alert_org.id, name="Main")
    db.add(location)
    db.flush()

    low_item = Item(org_id=alert_org.id, code="LOW-1", name="Low Item", uom_id=stock_uom.id, is_stock_item=True)
    high_item = Item(org_id=alert_org.id, code="HIGH-1", name="High Item", uom_id=stock_uom.id, is_stock_item=True)
    db.add_all([low_item, high_item])
    db.flush()

    db.add_all(
        [
            ItemLocation(item_id=low_item.id, location_id=location.id, min_qty=5),
            ItemLocation(item_id=high_item.id, location_id=location.id, min_qty=5),
        ]
    )
    db.flush()

    _posted_receipt(db, alert_org.id, low_item.id, stock_uom.id, location.id, qty=3)
    _posted_receipt(db, alert_org.id, high_item.id, stock_uom.id, location.id, qty=8)

    monkeypatch.setattr(ConfigService, "flag", staticmethod(lambda *_args, **_kwargs: True))
    monkeypatch.setattr(jobs.Aras, "get_db", lambda: iter([db]))

    sent = []
    monkeypatch.setattr(
        jobs,
        "_send_email",
        lambda _db, recipient, subject, text, html: sent.append(
            {"recipient": recipient, "subject": subject, "text": text, "html": html}
        ),
    )

    jobs.send_low_stock_digest()

    assert len(sent) == 1
    assert sent[0]["recipient"] == "ops@example.com"
    assert "Low Item" in sent[0]["text"]
    assert "High Item" not in sent[0]["text"]


# gpt-5
def test_low_stock_digest_respects_disabled_toggle(db, alert_org, stock_uom, monkeypatch):
    from apps.stock import jobs
    from apps.stock.models import Item, ItemLocation, Location
    from core.lib.config import ConfigService

    location = Location(org_id=alert_org.id, name="Main")
    db.add(location)
    db.flush()

    item = Item(org_id=alert_org.id, code="LOW-2", name="Disabled Item", uom_id=stock_uom.id, is_stock_item=True)
    db.add(item)
    db.flush()
    db.add(ItemLocation(item_id=item.id, location_id=location.id, min_qty=5))
    db.flush()
    _posted_receipt(db, alert_org.id, item.id, stock_uom.id, location.id, qty=1)

    monkeypatch.setattr(ConfigService, "flag", staticmethod(lambda *_args, **_kwargs: False))
    monkeypatch.setattr(jobs.Aras, "get_db", lambda: iter([db]))

    sent = []
    monkeypatch.setattr(
        jobs,
        "_send_email",
        lambda *_args, **_kwargs: sent.append(True),
    )

    jobs.send_low_stock_digest()

    assert sent == []
