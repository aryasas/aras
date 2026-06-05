from sqlalchemy.orm import Session
from ..models import DeliveryNote, StockMovement, StockMovementLine, Item, ItemCategory
from core.manager.workflow_manager import WorkflowManager
from core.service_registry import ServiceRegistry
from core import Aras


# SalesInvoice/SalesInvoiceLine were stale names (class never existed in accounting models).
# Correct models are OutflowInvoice/OutflowInvoiceLine, resolved at call time via ServiceRegistry.


def _get_OutflowInvoice():
    cls = ServiceRegistry.get("OutflowInvoice")
    if cls is None:
        raise RuntimeError("AccountingService 'OutflowInvoice' not registered; is the accounting app installed?")
    return cls


def _get_OutflowInvoiceLine():
    cls = ServiceRegistry.get("OutflowInvoiceLine")
    if cls is None:
        raise RuntimeError("AccountingService 'OutflowInvoiceLine' not registered; is the accounting app installed?")
    return cls


class StockWorkflowService:
    @staticmethod
    def post_delivery_note(db, delivery_note_id, user):
        delivery_note = db.get(DeliveryNote, delivery_note_id)
        if not delivery_note:
            raise ValueError(f"DeliveryNote with ID {delivery_note_id} not found.")
        if delivery_note.status != "Confirmed":
            raise ValueError(f"DeliveryNote must be 'Confirmed' to be posted. Current status: {delivery_note.status}")

        movement = StockMovement(
            org_id=delivery_note.org_id,
            move_type="delivery",
            origin_model="stock_delivery_notes",
            origin_id=delivery_note.id,
            status="Draft",
            doc_date=delivery_note.doc_date,
            notes=f"Auto-generated from Delivery Note {delivery_note.number}"
        )
        db.add(movement)
        db.flush()

        for line in delivery_note.lines:
            sm_line = StockMovementLine(
                movement_id=movement.id,
                item_id=line.item_id,
                qty=line.qty,
                uom_id=line.uom_id,
                from_location_id=line.location_id,
                unit_price=line.unit_price
            )
            db.add(sm_line)

        WorkflowManager.trigger_action(movement, "Post", db, user)
        return movement

    # claude-sonnet-4-6
    @staticmethod
    def create_invoice_from_delivery(db, delivery_note_id, user):
        OutflowInvoice = _get_OutflowInvoice()
        OutflowInvoiceLine = _get_OutflowInvoiceLine()

        delivery_note = db.get(DeliveryNote, delivery_note_id)
        if not delivery_note:
            raise ValueError(f"DeliveryNote with ID {delivery_note_id} not found.")

        invoice = OutflowInvoice(
            org_id=delivery_note.org_id,
            party_id=delivery_note.party_id,
            doc_date=delivery_note.doc_date,
            status="Draft",
            origin_model="stock_delivery_notes",
            origin_id=delivery_note.id,
            notes=f"Auto-generated from Delivery Note {delivery_note.number}"
        )
        db.add(invoice)
        db.flush()

        for line in delivery_note.lines:
            inv_line = OutflowInvoiceLine(
                invoice_id=invoice.id,
                item_id=line.item_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
            )
            db.add(inv_line)

        return invoice
