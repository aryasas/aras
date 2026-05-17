from sqlalchemy.orm import Session, object_session
from ..models import InflowOrder, InflowInvoice, InflowInvoiceLine, InflowInvoiceCharge, \
    OutflowOrder, OutflowInvoice, OutflowInvoiceLine, OutflowInvoiceCharge

class DocumentConversionService:
    @staticmethod
    def create_invoice_from_inflow_order(db: Session, order: InflowOrder):
        if order.status not in ("Confirmed", "Partial"):
            return {"error": f"Order {order.number} must be confirmed before invoicing."}
            
        invoice = InflowInvoice(
            org_id=order.org_id,
            party_id=order.party_id,
            currency_id=order.currency_id,
            notes=f"Generated from Inflow Order {order.number}",
            subtotal=order.subtotal,
            total_charge=order.total_charge,
            total_amount=order.total_amount,
            status="Draft"
        )
        db.add(invoice)
        db.flush()
        
        # Copy Lines
        for line in order.lines:
            inv_line = InflowInvoiceLine(
                invoice_id=invoice.id,
                product_id=line.product_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
                discount=line.discount,
                description=f"Ref: {order.number}"
            )
            db.add(inv_line)
            
        # Copy Charges
        for charge in order.charges:
            inv_charge = InflowInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount
            )
            db.add(inv_charge)
            
        order.status = "Posted" # Or "Completed"
        db.commit()
        return {"id": invoice.id, "number": invoice.number, "message": f"Invoice {invoice.number} created successfully."}

    @staticmethod
    def create_invoice_from_outflow_order(db: Session, order: OutflowOrder):
        if order.status not in ("Confirmed", "Partial"):
            return {"error": f"Order {order.number} must be confirmed before invoicing."}
            
        invoice = OutflowInvoice(
            org_id=order.org_id,
            party_id=order.party_id,
            currency_id=order.currency_id,
            notes=f"Generated from Outflow Order {order.number}",
            subtotal=order.subtotal,
            total_charge=order.total_charge,
            total_amount=order.total_amount,
            status="Draft"
        )
        db.add(invoice)
        db.flush()
        
        # Copy Lines
        for line in order.lines:
            inv_line = OutflowInvoiceLine(
                invoice_id=invoice.id,
                product_id=line.product_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=line.unit_price,
                discount=line.discount,
                description=f"Ref: {order.number}"
            )
            db.add(inv_line)
            
        # Copy Charges
        for charge in order.charges:
            inv_charge = OutflowInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount
            )
            db.add(inv_charge)
            
        order.status = "Posted"
        db.commit()
        return {"id": invoice.id, "number": invoice.number, "message": f"Invoice {invoice.number} created successfully."}
