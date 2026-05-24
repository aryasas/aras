from sqlalchemy.orm import Session
from ..models import DeliveryNote, StockMovement, StockMovementLine, Item, ItemCategory
from apps.accounting.models import SalesInvoice, SalesInvoiceLine
from apps.accounting.services.journal import JournalService
from core.logic.workflow import WorkflowManager
from core import Aras

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
            origin_model="erp_stock_delivery_notes",
            origin_id=delivery_note.id,
            status="Draft",
            doc_date=delivery_note.doc_date,
            notes=f"Auto-generated from Delivery Note {delivery_note.number}"
        )
        db.add(movement)
        db.flush() # Flush to get movement.id

        for line in delivery_note.lines:
            sm_line = StockMovementLine(
                movement_id=movement.id,
                item_id=line.item_id,
                qty=line.qty,
                uom_id=line.uom_id,
                from_location_id=line.location_id, # Assuming DeliveryNoteLine has location_id
                unit_price=line.unit_price # Assuming DeliveryNoteLine has unit_price
            )
            db.add(sm_line)
        
        # Trigger the workflow transition which will call post_stock_movement
        WorkflowManager.trigger_action(movement, "Post", db, user)
        return movement

    @staticmethod
    def create_invoice_from_delivery(db, delivery_note_id, user):
        delivery_note = db.get(DeliveryNote, delivery_note_id)
        if not delivery_note:
            raise ValueError(f"DeliveryNote with ID {delivery_note_id} not found.")

        invoice = SalesInvoice(
            org_id=delivery_note.org_id,
            party_id=delivery_note.party_id,
            doc_date=delivery_note.doc_date,
            status="Draft",
            origin_model="erp_stock_delivery_notes",
            origin_id=delivery_note.id,
            notes=f"Auto-generated from Delivery Note {delivery_note.number}"
        )
        db.add(invoice)
        db.flush() # Flush to get invoice.id

        for line in delivery_note.lines:
            inv_line = SalesInvoiceLine(
                invoice_id=invoice.id,
                item_id=line.item_id, # Use item_id
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
            )
            db.add(inv_line)
        
        return invoice
