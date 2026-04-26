"""
Stock posting service — on StockMovement.post():
1. Update StockValuation (qty + avg cost)
2. Auto-create AccJournalEntry from product category accounts
"""
import logging
from datetime import datetime
from decimal import Decimal

from arasCore.lib.extensions import db
from aras.app_erp.erp_stock.models import StockMovement, StockValuation
from aras.app_erp.erp_acc.models import AccJournalEntry, AccJournalLine

logger = logging.getLogger(__name__)


def _valuation(company_id, product_id, location_id):
    val, _ = StockValuation.get_or_create(
        {"qty_on_hand": 0, "avg_cost": 0, "total_value": 0},
        company_id=company_id, product_id=product_id, location_id=location_id,
    )
    return val


def _update_avg_cost(val, qty_in, unit_cost):
    old_total = Decimal(str(val.qty_on_hand)) * Decimal(str(val.avg_cost))
    new_total = Decimal(str(qty_in)) * Decimal(str(unit_cost))
    new_qty   = Decimal(str(val.qty_on_hand)) + Decimal(str(qty_in))
    if new_qty > 0:
        val.avg_cost    = (old_total + new_total) / new_qty
        val.qty_on_hand = new_qty
        val.total_value = new_qty * val.avg_cost
    return val


def post_movement(movement_id: int, posted_by_id: int = None) -> StockMovement:
    mv = StockMovement.get_or_404(movement_id)
    if mv.state != "confirmed":
        raise ValueError(f"Movement {mv.name} is in state '{mv.state}', expected 'confirmed'.")

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

        if amount == 0:
            continue

        total_amount += amount
        acc_stock    = category.account_stock_id    if category else None
        acc_cogs     = category.account_cogs_id     if category else None
        acc_purchase = category.account_purchase_id if category else None

        # receipt: DR stock / CR purchase_clearing
        # delivery: DR cogs / CR stock
        # adjustment: DR/CR stock variance
        if mv.move_type == "receipt" and acc_stock and acc_purchase:
            _add_line(entry, acc_stock,    amount, 0,      0)
            _add_line(entry, acc_purchase, 0,      amount, 0)

        elif mv.move_type in ("delivery", "return") and acc_cogs and acc_stock:
            _add_line(entry, acc_cogs,  amount, 0,      0)
            _add_line(entry, acc_stock, 0,      amount, 0)

        elif mv.move_type in ("adjustment", "opening") and acc_stock:
            variance_acc = category.account_variance_id if category else acc_stock
            if amount > 0:
                _add_line(entry, acc_stock,    amount,      0,      0)
                _add_line(entry, variance_acc, 0,           amount, 0)
            else:
                abs_amt = abs(amount)
                _add_line(entry, variance_acc, abs_amt, 0,       0)
                _add_line(entry, acc_stock,    0,       abs_amt, 0)

        if mv.move_type in ("receipt", "opening", "adjustment"):
            src = _valuation(mv.company_id, line.product_id, mv.dst_location_id or 0)
            _update_avg_cost(src, qty_base, cost)
            # avg_cost is already stored in StockValuation

        elif mv.move_type in ("delivery", "scrap"):
            src = _valuation(mv.company_id, line.product_id, mv.src_location_id or 0)
            src.qty_on_hand = max(Decimal("0"), Decimal(str(src.qty_on_hand)) - qty_base)
            src.total_value = src.qty_on_hand * Decimal(str(src.avg_cost))

        elif mv.move_type == "internal":
            if mv.src_location_id:
                s = _valuation(mv.company_id, line.product_id, mv.src_location_id)
                s.qty_on_hand = max(Decimal("0"), Decimal(str(s.qty_on_hand)) - qty_base)
                s.total_value = s.qty_on_hand * Decimal(str(s.avg_cost))
            if mv.dst_location_id:
                d = _valuation(mv.company_id, line.product_id, mv.dst_location_id)
                _update_avg_cost(d, qty_base, Decimal(str(s.avg_cost)) if mv.src_location_id else cost)

    entry.amount_total = total_amount
    entry.state        = "posted"
    entry.posted_at    = datetime.utcnow()
    if posted_by_id:
        entry.posted_by = posted_by_id

    mv.journal_entry_id = entry.id
    mv.state            = "posted"

    db.session.commit()
    logger.info(f"[stock.posting] posted movement {mv.name} → journal entry {entry.name}")
    return mv


def _add_line(entry, account_id, debit, credit, seq=0):
    db.session.add(AccJournalLine(
        entry_id=entry.id, sequence=seq,
        account_id=account_id, debit=debit, credit=credit,
    ))
