"""
Stock posting service — on StockMovement.post():
1. Compute running_avg_cost per line (WAC snapshot)
2. Auto-create AccJournalEntry from product category accounts
"""
import logging
from datetime import datetime
from decimal import Decimal

from arasCore.lib.core.extensions import db
from aras.erp.erp_stock.models import StockMovement
from aras.erp.erp_acc.models import AccJournalEntry, AccJournalLine

logger = logging.getLogger(__name__)

IN_TYPES = ("receipt", "opening", "adjustment", "return")


def _compute_running_wac(product_id: int, location_id: int, company_id: int,
                          qty_in: Decimal, unit_cost: Decimal,
                          by_location: bool) -> Decimal:
    """
    Calculate new weighted average cost after adding qty_in at unit_cost.
    Uses current computed qty+value as the running base.
    """
    from aras.erp.erp_stock.services.stock_compute import compute_qty, compute_avg_cost

    if by_location and location_id:
        cur_qty  = compute_qty(product_id, location_id=location_id, company_id=company_id)
        cur_cost = compute_avg_cost(product_id, location_id=location_id, company_id=company_id)
    else:
        cur_qty  = compute_qty(product_id, company_id=company_id)
        cur_cost = compute_avg_cost(product_id, company_id=company_id)

    old_total = cur_qty * cur_cost
    new_total = qty_in * unit_cost
    new_qty   = cur_qty + qty_in
    if new_qty > 0:
        return (old_total + new_total) / new_qty
    return unit_cost


def post_movement(movement_id: int, posted_by_id: int = None, skip_journal: bool = False) -> StockMovement:
    mv = StockMovement.get_or_404(movement_id)
    if mv.state != "confirmed":
        raise ValueError(f"Movement {mv.name} is in state '{mv.state}', expected 'confirmed'.")

    from aras.erp.erp_core.models.company import Company
    company = Company.get(mv.company_id)
    by_location = bool(company and company.avg_cost_by_location)

    entry = None
    if not skip_journal:
        entry = AccJournalEntry(
            company_id=mv.company_id, name=f"SM/{mv.name}",
            date_entry=mv.date_move, reference=mv.reference or mv.name,
            narrative=f"Auto: {mv.move_type} — {mv.name}", state="draft",
            origin_model="stock_movement", origin_id=mv.id,
            fiscal_period_id=mv.fiscal_period_id,
        )
        db.session.add(entry)
        db.session.flush()

    total_amount = Decimal("0")

    for line in mv.lines:
        product  = line.product
        category = product.category
        qty_base = Decimal(str(line.qty_base))
        cost     = Decimal(str(line.unit_cost))
        amount   = qty_base * cost

        if not skip_journal and amount > 0:
            total_amount += amount
            acc_stock    = category.account_stock_id    if category else None
            acc_cogs     = category.account_cogs_id     if category else None
            acc_purchase = category.account_purchase_id if category else None

            if mv.move_type == "receipt" and acc_stock and acc_purchase:
                _add_line(entry, acc_stock,    amount, 0,      0)
                _add_line(entry, acc_purchase, 0,      amount, 0)

            elif mv.move_type in ("delivery", "return") and acc_cogs and acc_stock:
                _add_line(entry, acc_cogs,  amount, 0,      0)
                _add_line(entry, acc_stock, 0,      amount, 0)

            elif mv.move_type in ("adjustment", "opening") and acc_stock:
                variance_acc = category.account_variance_id if category else acc_stock
                if amount > 0:
                    _add_line(entry, acc_stock,    amount,  0,      0)
                    _add_line(entry, variance_acc, 0,       amount, 0)
                else:
                    abs_amt = abs(amount)
                    _add_line(entry, variance_acc, abs_amt, 0,       0)
                    _add_line(entry, acc_stock,    0,       abs_amt, 0)

        # Compute and store running_avg_cost snapshot for IN movements
        if mv.move_type in IN_TYPES:
            dst_loc = mv.dst_location_id or 0
            line.running_avg_cost = _compute_running_wac(
                line.product_id, dst_loc, mv.company_id,
                qty_base, cost, by_location
            )
        elif mv.move_type == "internal" and mv.dst_location_id:
            # Use src location avg as the cost carried over
            from aras.erp.erp_stock.services.stock_compute import compute_avg_cost
            src_avg = compute_avg_cost(line.product_id, location_id=mv.src_location_id,
                                       company_id=mv.company_id)
            line.running_avg_cost = _compute_running_wac(
                line.product_id, mv.dst_location_id, mv.company_id,
                qty_base, src_avg, by_location
            )

    if not skip_journal and entry:
        entry.amount_total = total_amount
        entry.state        = "posted"
        entry.posted_at    = datetime.utcnow()
        if posted_by_id:
            entry.posted_by = posted_by_id
        mv.journal_entry_id = entry.id

    mv.state = "posted"

    db.session.commit()
    logger.info(f"[stock.posting] posted movement {mv.name} → journal entry {entry.name if entry else 'none'}")
    return mv


def _add_line(entry, account_id, debit, credit, seq=0):
    db.session.add(AccJournalLine(
        entry_id=entry.id, sequence=seq,
        account_id=account_id, debit=debit, credit=credit,
    ))
