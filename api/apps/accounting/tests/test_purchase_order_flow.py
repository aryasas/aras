import uuid
from types import SimpleNamespace
from typing import Optional

import pytest

from core.exceptions import ValidationException


def _line(item_id: int, qty: float, unit_price: float, *, quantity_received: Optional[float] = None):
    return SimpleNamespace(
        item_id=item_id,
        qty=qty,
        unit_price=unit_price,
        quantity_received=qty if quantity_received is None else quantity_received,
        unit_cost=unit_price,
    )


# gpt-5
def test_three_way_match_exact_match():
    from apps.accounting.services.three_way_match import evaluate_three_way_match

    result = evaluate_three_way_match(
        purchase_order=SimpleNamespace(lines=[_line(1, 10, 50)]),
        goods_receipt=SimpleNamespace(lines=[_line(1, 10, 50, quantity_received=10)]),
        invoice=SimpleNamespace(lines=[_line(1, 10, 50)]),
        qty_tolerance_pct=0,
        price_tolerance_pct=0,
    )

    assert result["matched"] is True
    assert result["discrepancies"] == []


# gpt-5
def test_three_way_match_flags_over_receipt_beyond_tolerance():
    from apps.accounting.services.three_way_match import evaluate_three_way_match

    result = evaluate_three_way_match(
        purchase_order=SimpleNamespace(lines=[_line(1, 10, 50)]),
        goods_receipt=SimpleNamespace(lines=[_line(1, 10, 50, quantity_received=11)]),
        invoice=SimpleNamespace(lines=[_line(1, 11, 50)]),
        qty_tolerance_pct=5,
        price_tolerance_pct=0,
    )

    assert result["matched"] is False
    assert any("received qty 11.00 exceeds ordered qty 10.00" in msg for msg in result["discrepancies"])


# gpt-5
def test_three_way_match_flags_price_above_po_beyond_tolerance():
    from apps.accounting.services.three_way_match import evaluate_three_way_match

    result = evaluate_three_way_match(
        purchase_order=SimpleNamespace(lines=[_line(1, 10, 100)]),
        goods_receipt=SimpleNamespace(lines=[_line(1, 10, 100, quantity_received=10)]),
        invoice=SimpleNamespace(lines=[_line(1, 10, 107)]),
        qty_tolerance_pct=0,
        price_tolerance_pct=5,
    )

    assert result["matched"] is False
    assert any("invoiced unit price 107.00 exceeds PO unit price 100.00" in msg for msg in result["discrepancies"])


# gpt-5
def test_three_way_match_accepts_within_tolerance_variance():
    from apps.accounting.services.three_way_match import evaluate_three_way_match

    result = evaluate_three_way_match(
        purchase_order=SimpleNamespace(lines=[_line(1, 10, 100)]),
        goods_receipt=SimpleNamespace(lines=[_line(1, 10, 100, quantity_received=10.4)]),
        invoice=SimpleNamespace(lines=[_line(1, 10.2, 104)]),
        qty_tolerance_pct=5,
        price_tolerance_pct=5,
    )

    assert result["matched"] is True
    assert result["discrepancies"] == []


@pytest.fixture
def po_uom(db):
    from plugins.commerce.models import Uom

    uom = Uom(name=f"PO-UOM-{str(uuid.uuid4())[:4]}")
    db.add(uom)
    db.flush()
    return uom


@pytest.fixture
def po_currency(db):
    from core.workspace.models import Currency

    currency = Currency(name="USD", code=f"PO{str(uuid.uuid4())[:4]}", symbol="$")
    db.add(currency)
    db.flush()
    return currency


@pytest.fixture
def supplier(db, org):
    from apps.party.models import Party

    party = Party(name=f"Supplier {str(uuid.uuid4())[:4]}", role="supplier", org_id=org.id)
    db.add(party)
    db.flush()
    return party


@pytest.fixture
def warehouse(db, org):
    from apps.stock.models import Location

    location = Location(name=f"WH {str(uuid.uuid4())[:4]}", org_id=org.id, location_type="Internal")
    db.add(location)
    db.flush()
    return location


@pytest.fixture
def po_item(db, org, po_uom):
    from apps.stock.models import Item

    item = Item(
        name="PO Item",
        code=f"PO-ITEM-{str(uuid.uuid4())[:4]}",
        org_id=org.id,
        uom_id=po_uom.id,
        uom_purchase_id=po_uom.id,
        is_stock_item=True,
    )
    db.add(item)
    db.flush()
    return item


# gpt-5
def test_purchase_order_to_grn_to_invoice_flow(db, org, supplier, po_currency, po_uom, warehouse, po_item):
    from apps.accounting.models import PurchaseOrder, PurchaseOrderLine, GoodsReceiptNote, OutflowInvoice, OutflowInvoiceLine
    from apps.stock.models import StockMovement

    purchase_order = PurchaseOrder(
        org_id=org.id,
        number=f"PO-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        currency_id=po_currency.id,
        location_id=warehouse.id,
        doc_type="Order",
        status="Approved",
    )
    db.add(purchase_order)
    db.flush()
    db.add(
        PurchaseOrderLine(
            purchase_order_id=purchase_order.id,
            item_id=po_item.id,
            qty=10,
            uom_id=po_uom.id,
            unit_price=50,
            discount=0,
        )
    )
    db.flush()
    db.refresh(purchase_order)
    purchase_order.recalc()

    action_result = purchase_order.create_grn(db)
    grn_id = action_result["data"]["id"]
    grn = db.get(GoodsReceiptNote, grn_id)

    assert grn.purchase_order_id == purchase_order.id
    assert grn.purchase_order_ref == purchase_order.number
    assert len(grn.lines) == 1
    assert float(grn.lines[0].quantity_received) == 10.0

    receive_result = grn.receive(db)
    db.flush()

    assert receive_result["data"]["status"] == "Received"
    assert purchase_order.status == "Received"
    assert db.query(StockMovement).filter_by(org_id=org.id, number=f"SM-GRN-{grn.number}").count() == 1

    invoice = OutflowInvoice(
        org_id=org.id,
        number=f"BILL-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        currency_id=po_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        OutflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=po_item.id,
            qty=10,
            uom_id=po_uom.id,
            unit_price=50,
            discount=0,
        )
    )
    db.flush()
    db.refresh(invoice)

    match_result = grn.match_invoice(db, grn._MatchInvoiceInput(invoice_id=invoice.id))
    db.flush()

    assert match_result["data"]["status"] == "Matched"
    assert invoice.grn_id == grn.id
    assert invoice.purchase_order_id == purchase_order.id
    assert purchase_order.status == "Closed"


# gpt-5
def test_match_invoice_rejects_mismatch_without_partial_commit(db, org, supplier, po_currency, po_uom, warehouse, po_item):
    from apps.accounting.models import GoodsReceiptNote, PurchaseOrder, PurchaseOrderLine, OutflowInvoice, OutflowInvoiceLine

    purchase_order = PurchaseOrder(
        org_id=org.id,
        number=f"PO-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        currency_id=po_currency.id,
        location_id=warehouse.id,
        doc_type="Order",
        status="Approved",
    )
    db.add(purchase_order)
    db.flush()
    db.add(
        PurchaseOrderLine(
            purchase_order_id=purchase_order.id,
            item_id=po_item.id,
            qty=10,
            uom_id=po_uom.id,
            unit_price=50,
            discount=0,
        )
    )
    db.flush()
    db.refresh(purchase_order)

    grn = purchase_order.create_grn(db)
    grn_model = db.get(GoodsReceiptNote, grn["data"]["id"])
    grn_model.receive(db)
    db.flush()

    invoice = OutflowInvoice(
        org_id=org.id,
        number=f"BAD-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        currency_id=po_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        OutflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=po_item.id,
            qty=10,
            uom_id=po_uom.id,
            unit_price=55,
            discount=0,
        )
    )
    db.flush()

    with pytest.raises(ValidationException, match="invoiced unit price 55.00 exceeds PO unit price 50.00"):
        grn_model.match_invoice(db, grn_model._MatchInvoiceInput(invoice_id=invoice.id))

    assert invoice.grn_id is None
    assert invoice.purchase_order_id is None
    assert grn_model.status == "Received"
    assert purchase_order.status == "Received"


# gpt-5
def test_grn_legacy_match_path_still_works(db, org, supplier, po_currency, po_uom, warehouse, po_item):
    from apps.accounting.models import GoodsReceiptNote, GoodsReceiptLine, OutflowInvoice, OutflowInvoiceLine

    grn = GoodsReceiptNote(
        org_id=org.id,
        number=f"GRN-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        purchase_order_ref="LEGACY-REF",
        warehouse_id=warehouse.id,
        status="Draft",
    )
    db.add(grn)
    db.flush()
    db.add(
        GoodsReceiptLine(
            grn_id=grn.id,
            item_id=po_item.id,
            quantity_received=3,
            unit_cost=20,
            qty=3,
        )
    )
    db.flush()

    grn.receive(db)
    db.flush()

    invoice = OutflowInvoice(
        org_id=org.id,
        number=f"LEG-{str(uuid.uuid4())[:8]}",
        party_id=supplier.id,
        currency_id=po_currency.id,
        doc_type="Invoice",
        status="Draft",
    )
    db.add(invoice)
    db.flush()
    db.add(
        OutflowInvoiceLine(
            invoice_id=invoice.id,
            item_id=po_item.id,
            qty=3,
            uom_id=po_uom.id,
            unit_price=20,
            discount=0,
        )
    )
    db.flush()

    result = grn.match_invoice(db, grn._MatchInvoiceInput(invoice_id=invoice.id))

    assert result["data"]["status"] == "Matched"
    assert invoice.grn_id == grn.id
