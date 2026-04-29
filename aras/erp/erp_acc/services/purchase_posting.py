"""
acc.purchase_posting — post AccPurchaseInvoice:
  1. Journal: DR inventory / CR payable per product category
  2. StockMovement receipt -> post_movement (updates valuation)
"""
from decimal import Decimal
from datetime import date as date_type

from arasCore.lib.core.extensions import db
from aras.erp.erp_acc.models.invoice import AccPurchaseInvoice
from aras.erp.erp_acc.services.posting import post_journal, get_default_account
from aras.erp.erp_stock.models.product import StockProduct
from aras.erp.erp_stock.models.warehouse import StockLocation
from aras.erp.erp_stock.services.posting import post_movement


def post_purchase_invoice(invoice_id: int, warehouse_id: int = None) -> AccPurchaseInvoice:
    inv = AccPurchaseInvoice.query.get_or_404(invoice_id)
    if inv.state != "draft":
        raise ValueError(f"Invoice {inv.name} is already {inv.state}")

    company_id   = inv.company_id
    journal_lines = []
    stock_lines   = []

    for line in inv.lines:
        qty      = Decimal(str(line.qty or 0))
        price    = Decimal(str(line.unit_price or 0))
        subtotal = Decimal(str(line.subtotal or (qty * price)))

        product   = StockProduct.get(line.product_id) if line.product_id else None
        category  = product.category if product and product.category else None

        acc_stock    = (category.account_stock_id    if category else None) or get_default_account(company_id, "stock_default")
        acc_purchase = (category.account_purchase_id if category else None) or get_default_account(company_id, "payable_default")

        if acc_stock:
            journal_lines.append({"account_id": acc_stock,    "debit": float(subtotal), "credit": 0})
        if acc_purchase:
            journal_lines.append({"account_id": acc_purchase, "debit": 0, "credit": float(subtotal)})

        if product and getattr(product, "is_stock_item", True):
            stock_lines.append({"product_id": line.product_id, "uom_id": line.uom_id,
                                 "qty": qty, "unit_cost": price})

    if journal_lines:
        entry = post_journal(
            company_id=company_id,
            date=inv.invoice_date or date_type.today(),
            lines=journal_lines,
            narrative=f"Purchase: {inv.name}",
            origin=("acc_purchase_invoice", inv.id),
        )
        inv.journal_entry_id = entry.id

    if stock_lines and warehouse_id:
        from aras.erp.erp_stock.models.movement import StockMovement, StockMovementLine
        from aras.erp.erp_core.models.sequence import Sequence
        from aras.erp.erp_core.services import sequence as seq_svc
        seq  = (Sequence.find(code="stock.receipt", company_id=company_id)
                or Sequence.find(code="stock.move", company_id=company_id))
        name = seq_svc.next_number_for_seq(seq) if seq else f"GRN/{company_id}/{inv.name}"

        dst_loc = StockLocation.query.filter_by(
            warehouse_id=warehouse_id, location_type="internal", is_active=True
        ).first()

        if dst_loc:
            mv = StockMovement(
                company_id=company_id,
                name=name,
                move_type="receipt",
                date_move=inv.invoice_date or date_type.today(),
                dst_location_id=dst_loc.id,
                state="confirmed",
                origin_model="acc_purchase_invoice",
                origin_id=inv.id,
            )
            db.session.add(mv)
            db.session.flush()

            for sl in stock_lines:
                db.session.add(StockMovementLine(
                    movement_id=mv.id,
                    product_id=sl["product_id"],
                    uom_id=sl["uom_id"],
                    qty=sl["qty"],
                    qty_base=sl["qty"],  # same as qty (base UOM purchase)
                    unit_cost=sl["unit_cost"],
                    total_cost=sl["qty"] * sl["unit_cost"],
                ))
            db.session.flush()
            post_movement(mv.id)

    inv.state = "posted"
    db.session.commit()
    return inv
