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
def stock_item(db, org, stock_uom):
    from apps.stock.models import Item

    item = Item(
        org_id=org.id,
        code="SKU-1",
        name="Sample Item",
        uom_id=stock_uom.id,
        is_stock_item=True,
    )
    db.add(item)
    db.flush()
    return item


# claude-opus-4-8
def _receipt_layer(db, org_id: int, item_id: int, uom_id: int, qty: float, unit_cost: float):
    from apps.stock.models import StockMovement, StockMovementLine

    movement = StockMovement(org_id=org_id, number="SM-1", move_type="receipt", status="Posted")
    db.add(movement)
    db.flush()
    line = StockMovementLine(
        movement_id=movement.id,
        item_id=item_id,
        qty=qty,
        uom_id=uom_id,
        unit_cost=unit_cost,
        qty_remaining=qty,
        to_location_id=None,
    )
    db.add(line)
    db.flush()
    return line


# claude-opus-4-8
def test_consume_blocks_oversell_when_zero_stock_disabled(db, org, stock_item, stock_uom):
    from apps.stock.services.valuation import InventoryValuationService
    from core.exceptions import ValidationException

    _receipt_layer(db, org.id, stock_item.id, stock_uom.id, qty=5, unit_cost=2.0)

    with pytest.raises(ValidationException, match="Insufficient stock"):
        InventoryValuationService.consume(db, stock_item.id, org.id, 6)


# claude-opus-4-8
def test_consume_allows_oversell_when_zero_stock_enabled(db, org, stock_item, stock_uom):
    from apps.stock.config_models import StockConfig
    from apps.stock.services.valuation import InventoryValuationService

    _receipt_layer(db, org.id, stock_item.id, stock_uom.id, qty=5, unit_cost=2.0)
    db.add(StockConfig(org_id=org.id, allow_zero_stock=True))
    db.flush()

    consumed = InventoryValuationService.consume(db, stock_item.id, org.id, 6)
    assert consumed == 10.0


# claude-opus-4-8
def test_consume_succeeds_with_available_stock(db, org, stock_item, stock_uom):
    from apps.stock.models import StockMovementLine
    from apps.stock.services.valuation import InventoryValuationService

    layer = _receipt_layer(db, org.id, stock_item.id, stock_uom.id, qty=5, unit_cost=2.0)

    consumed = InventoryValuationService.consume(db, stock_item.id, org.id, 3)

    db.refresh(layer)
    assert consumed == 6.0
    assert layer.qty_remaining == 2
