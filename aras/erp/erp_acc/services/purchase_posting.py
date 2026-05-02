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
from aras.erp.erp_stock.models.warehouse import StockLocation  # noqa
from aras.erp.erp_stock.services.posting import post_movement
from aras.erp.erp_stock.services.coa_resolver import resolve_stock_account, resolve_purchase_account


def post_purchase_invoice(invoice_id: int, location_id: int = None) -> AccPurchaseInvoice:
    inv = AccPurchaseInvoice.query.get_or_404(invoice_id)
    if inv.journal_entry_id:
        raise ValueError(f"Invoice {inv.name} already has a journal entry")
    if inv.state == "cancelled":
        raise ValueError(f"Invoice {inv.name} is cancelled")
    if not location_id:
        location_id = inv.location_id

    company_id   = inv.company_id
    journal_lines = []
    stock_lines   = []

    # Recompute totals from lines if header totals are zero
    computed_sub = sum(Decimal(str(l.subtotal or 0)) for l in inv.lines)
    if Decimal(str(inv.total or 0)) == 0 and computed_sub > 0:
        inv.subtotal = float(computed_sub)
        inv.total    = float(computed_sub)

    for line in inv.lines:
        qty      = Decimal(str(line.qty or 0))
        price    = Decimal(str(line.unit_price or 0))
        subtotal = Decimal(str(line.subtotal or (qty * price)))

        product   = StockProduct.get(line.product_id) if line.product_id else None

        if product:
            acc_stock    = resolve_stock_account(product, company_id)
            acc_purchase = resolve_purchase_account(product, company_id)
            if not acc_stock:
                acc_stock = get_default_account(company_id, "stock_default")
            if not acc_purchase:
                acc_purchase = get_default_account(company_id, "payable_default")
        else:
            acc_stock    = get_default_account(company_id, "stock_default")
            acc_purchase = get_default_account(company_id, "payable_default")

        journal_lines.append({"account_id": acc_stock,    "debit": float(subtotal), "credit": 0})
        journal_lines.append({"account_id": acc_purchase, "debit": 0, "credit": float(subtotal)})

        if product and getattr(product, "is_stock_item", True):
            uom_id = line.uom_id or product.uom_id
            stock_lines.append({"product_id": line.product_id, "uom_id": uom_id,
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

    if stock_lines and location_id:
        from aras.erp.erp_stock.models.movement import StockMovement, StockMovementLine
        from aras.erp.erp_core.models.sequence import Sequence
        from aras.erp.erp_core.services import sequence as seq_svc
        seq  = (Sequence.find(code="stock.receipt", company_id=company_id)
                or Sequence.find(code="stock.move", company_id=company_id))
        name = seq_svc.next_number_for_seq(seq) if seq else f"GRN/{company_id}/{inv.name}"

        dst_loc = StockLocation.get(location_id)

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
            post_movement(mv.id, skip_journal=True)

    inv.state = "posted"
    db.session.commit()
    return inv
