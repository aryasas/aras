from sqlalchemy.orm import Session, object_session
from ..models import SalesOrder, SalesInvoice, SalesInvoiceLine, SalesInvoiceCharge, \
    PurchaseOrder, PurchaseInvoice, PurchaseInvoiceLine, PurchaseInvoiceCharge

class DocumentConversionService:
    @staticmethod
    def create_invoice_from_sales_order(db: Session, order: SalesOrder):
        if order.status not in ("Confirmed", "Partial"):
            return {"error": f"Order {order.number} must be confirmed before invoicing."}
            
        invoice = SalesInvoice(
            company_id=order.company_id,
            customer_id=order.customer_id,
            currency_id=order.currency_id,
            notes=f"Generated from Sales Order {order.number}",
            subtotal=order.subtotal,
            total_charge=order.total_charge,
            total_amount=order.total_amount,
            status="Draft"
        )
        db.add(invoice)
        db.flush()
        
        # Copy Lines
        for line in order.lines:
            inv_line = SalesInvoiceLine(
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
            inv_charge = SalesInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount
            )
            db.add(inv_charge)
            
        order.status = "Posted" # Or "Completed"
        db.commit()
        return {"id": invoice.id, "number": invoice.number, "message": f"Invoice {invoice.number} created successfully."}

    @staticmethod
    def create_invoice_from_purchase_order(db: Session, order: PurchaseOrder):
        if order.status not in ("Confirmed", "Partial"):
            return {"error": f"Order {order.number} must be confirmed before invoicing."}
            
        invoice = PurchaseInvoice(
            company_id=order.company_id,
            supplier_id=order.supplier_id,
            currency_id=order.currency_id,
            notes=f"Generated from Purchase Order {order.number}",
            subtotal=order.subtotal,
            total_charge=order.total_charge,
            total_amount=order.total_amount,
            status="Draft"
        )
        db.add(invoice)
        db.flush()
        
        # Copy Lines
        for line in order.lines:
            inv_line = PurchaseInvoiceLine(
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
            inv_charge = PurchaseInvoiceCharge(
                invoice_id=invoice.id,
                charge_id=charge.charge_id,
                amount=charge.amount
            )
            db.add(inv_charge)
            
        order.status = "Posted"
        db.commit()
        return {"id": invoice.id, "number": invoice.number, "message": f"Invoice {invoice.number} created successfully."}
