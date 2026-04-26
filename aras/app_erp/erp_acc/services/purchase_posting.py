"""
acc.purchase_posting — post AccPurchaseInvoice:
  1. Journal: DR inventory / CR payable per product category
  2. StockMovement receipt → post_movement (updates valuation + COGS journal)
"""
from decimal import Decimal
from datetime import date as date_type, datetime

from arasCore.lib.extensions import db
from aras.app_erp.erp_acc.models.invoice import AccPurchaseInvoice
from aras.app_erp.erp_acc.services.posting import post_journal
from aras.app_erp.erp_stock.models import StockMovement, StockMovementLine
from aras.app_erp.erp_stock.models.warehouse import StockLocation
from aras.app_erp.erp_stock.services.posting import post_movement
from aras.app_erp.erp_core.services import sequence as seq_svc


def _input_location():
    return (StockLocation.find(location_type="vendor", is_active=True)
            or StockLocation.find(location_type="virtual", is_active=True))


def _internal_location(warehouse_id):
    return StockLocation.find(warehouse_id=warehouse_id, location_type="internal", is_active=True)


def post_purchase_invoice(invoice_id: int, warehouse_id: int = None) -> AccPurchaseInvoice:
    inv = AccPurchaseInvoice.get_or_404(invoice_id)
    if inv.state not in ("draft",):
        raise ValueError(f"Invoice {inv.name} is in state '{inv.state}', expected 'draft'.")
    if not inv.lines:
        raise ValueError(f"Invoice {inv.name} has no lines.")

    journal_lines = []
    stock_lines   = []

    for line in inv.lines:
        if not line.product_id:
            # non-stock line: use line.account_id as DR, default payable as CR
            if line.account_id:
                journal_lines.append({"account_id": line.account_id,
                                      "debit": float(line.subtotal), "credit": 0})
            continue

        product  = line.product
        category = product.category if product else None
        subtotal = Decimal(str(line.subtotal))
        qty      = Decimal(str(line.qty))
        price    = subtotal / qty if qty else Decimal("0")

        acc_stock    = category.account_stock_id    if category else line.account_id
        acc_purchase = category.account_purchase_id if category else None

        if acc_stock:
            journal_lines.append({"account_id": acc_stock,    "debit": float(subtotal), "credit": 0})
        if acc_purchase:
            journal_lines.append({"account_id": acc_purchase, "debit": 0, "credit": float(subtotal)})

        if product and getattr(product, "is_stock_item", True):
            stock_lines.append({"product_id": line.product_id, "uom_id": line.uom_id,
                                 "qty": qty, "unit_cost": price})

    if not journal_lines:
        raise ValueError("No postable lines found.")

    entry = post_journal(
        company_id=inv.company_id,
        date=inv.invoice_date,
        lines=journal_lines,
        reference=inv.name,
        narrative=f"Purchase: {inv.vendor_name} — {inv.name}",
        origin=("acc_purchase_invoice", inv.id),
    )

    inv.journal_entry_id = entry.id
    inv.state            = "posted"

    # Create + post stock receipt if there are stock lines
    if stock_lines:
        dst_loc = (_internal_location(warehouse_id) if warehouse_id else None) or _input_location()
        src_loc = _input_location()

        mv_name = seq_svc.next_number("inventory.grn", inv.company_id)
        mv = StockMovement(
            company_id=inv.company_id,
            name=mv_name,
            move_type="receipt",
            state="confirmed",
            date_move=inv.invoice_date,
            src_location_id=src_loc.id if src_loc else None,
            dst_location_id=dst_loc.id if dst_loc else None,
            reference=inv.name,
            origin_model="acc_purchase_invoice",
            origin_id=inv.id,
            fiscal_period_id=inv.fiscal_period_id,
            is_manual=False,
        )
        db.session.add(mv)
        db.session.flush()

        for sl in stock_lines:
            db.session.add(StockMovementLine(
                movement_id=mv.id,
                product_id=sl["product_id"],
                uom_id=sl["uom_id"],
                qty=sl["qty"],
                qty_base=sl["qty"],
                unit_cost=sl["unit_cost"],
                total_cost=sl["qty"] * sl["unit_cost"],
            ))
        db.session.flush()

        db.session.commit()
        post_movement(mv.id)
    else:
        db.session.commit()

    return inv
