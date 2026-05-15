from sqlalchemy.orm import Session
from ..models import DeliveryNote, StockMovement, StockMovementLine, Product, ProductCategory
from ...accounting.models import SalesInvoice, SalesInvoiceLine, Account
from ...accounting.services.journal import JournalService
from .stock import StockComputeService

class StockWorkflowService:
    @staticmethod
    def post_delivery_note(db: Session, delivery: DeliveryNote):
        if delivery.status != "Draft":
            return {"error": f"Delivery Note is already {delivery.status}"}
            
        # 1. Create Stock Movement
        movement = StockMovement(
            company_id=delivery.company_id,
            move_type="Outgoing",
            from_location_id=delivery.location_id,
            status="Posted",
            notes=f"Auto-generated from {delivery.number}"
        )
        db.add(movement)
        db.flush()
        
        journal_lines = []
        total_valuation = 0.0
        
        for line in delivery.lines:
            product = db.query(Product).get(line.product_id)
            wac = StockComputeService.compute_avg_cost(db, line.product_id)
            amount = line.qty * wac
            total_valuation += amount
            
            mv_line = StockMovementLine(
                movement_id=movement.id,
                product_id=line.product_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_cost=wac
            )
            db.add(mv_line)
            
            # 2. Prepare Accounting Integration
            if product and product.category_id:
                category = db.query(ProductCategory).get(product.category_id)
                if category and category.account_cogs_id and category.account_stock_id:
                    # Debit COGS
                    journal_lines.append({
                        'account_id': category.account_cogs_id,
                        'debit': amount,
                        'credit': 0,
                        'description': f"COGS: {product.name} ({delivery.number})"
                    })
                    # Credit Inventory
                    journal_lines.append({
                        'account_id': category.account_stock_id,
                        'debit': 0,
                        'credit': amount,
                        'description': f"Inventory: {product.name} ({delivery.number})"
                    })

        # 3. Post Journal Entry
        if journal_lines and total_valuation > 0:
            try:
                JournalService.post_entry(
                    db,
                    delivery.company_id,
                    journal_lines,
                    reference=delivery.number,
                    narrative=f"Stock Valuation for {delivery.number}"
                )
            except Exception as e:
                db.rollback()
                return {"error": f"Accounting post failed: {str(e)}"}
            
        delivery.status = "Posted"
        db.commit()
        return True

    @staticmethod
    def create_invoice_from_delivery(db: Session, delivery: DeliveryNote):
        if delivery.status != "Posted":
            return {"error": "Delivery Note must be posted before invoicing."}
            
        invoice = SalesInvoice(
            company_id=delivery.company_id,
            customer_id=delivery.customer_id,
            status="Draft",
            notes=f"Generated from Delivery Note {delivery.number}"
        )
        db.add(invoice)
        db.flush()
        
        for line in delivery.lines:
            from ..services.price import PriceService
            unit_price = PriceService.get_price(db, line.product_id, uom_id=line.uom_id, qty=line.qty)

            inv_line = SalesInvoiceLine(
                invoice_id=invoice.id,
                product_id=line.product_id,
                qty=line.qty,
                uom_id=line.uom_id,
                unit_price=unit_price,
                discount=0,
                description=f"Ref: {delivery.number}"
            )
            db.add(inv_line)
            
        db.commit()
        return {"id": invoice.id, "number": invoice.number}
