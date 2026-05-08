"""acc.posting — the ONLY way to create posted journal entries."""
from decimal import Decimal
from datetime import date as date_type, datetime
from flask_login import current_user
from arasCore.lib.core.extensions import db
from app.erp.erp_acc.models.journal import AccJournalEntry, AccJournalLine
from app.erp.erp_main.models.fiscal import FiscalPeriod
from app.erp.erp_main.services import sequence as seq_svc
from app.erp.erp_main.services import audit as audit_svc
from arasCore.lib.core.action import action


def post_journal(
    company_id: int,
    date: date_type,
    lines: list,
    reference: str = "",
    narrative: str = "",
    origin: tuple = None,
    sequence_code: str = "accounting.journal",
    journal_code: str = None,  # kept for backwards compat, unused
) -> AccJournalEntry:
    """
    Atomically create and post a balanced journal entry.
    lines: list of dicts with keys: account_id, debit, credit,
           and optionally: partner_type, partner_id, currency_id,
           amount_currency, fx_rate, tax_base_amount,
           analytic_tag_id, description
    """
    period = _resolve_period(company_id, date)
    if period and period.state == "closed":
        raise ValueError(f"Fiscal period '{period.code}' is closed")

    if origin:
        existing = AccJournalEntry.query.filter_by(
            origin_model=origin[0], origin_id=origin[1]
        ).first()
        if existing:
            raise ValueError(f"Journal entry already exists for {origin[0]} #{origin[1]} ({existing.name})")

    lines = _merge_lines(lines)

    total_debit  = sum(Decimal(str(l.get("debit",  0))) for l in lines)
    total_credit = sum(Decimal(str(l.get("credit", 0))) for l in lines)
    if abs(total_debit - total_credit) > Decimal("0.01"):
        raise ValueError(f"Journal not balanced: debit={total_debit} credit={total_credit}")

    entry_name = seq_svc.next_code(company_id, sequence_code, default_format="JE-{YYYY}-{####}")

    user_id = None
    try:
        if current_user and current_user.is_authenticated:
            user_id = current_user.id
    except RuntimeError:
        pass

    entry = AccJournalEntry(
        company_id=company_id,
        name=entry_name,
        date_entry=date,
        reference=reference,
        narrative=narrative,
        state="posted",
        fiscal_period_id=period.id if period else None,
        amount_total=total_debit,
        posted_at=datetime.utcnow(),
        posted_by=user_id,
    )
    if origin:
        entry.origin_model, entry.origin_id = origin

    db.session.add(entry)
    db.session.flush()

    dr_lines = [l for l in lines if Decimal(str(l.get("debit",  0))) > 0]
    cr_lines = [l for l in lines if Decimal(str(l.get("credit", 0))) > 0]
    ordered  = dr_lines + cr_lines

    for i, l in enumerate(ordered):
        db.session.add(AccJournalLine(
            entry_id=entry.id,
            sequence=(i + 1) * 10,
            account_id=l["account_id"],
            partner_type=l.get("partner_type", "none"),
            partner_id=l.get("partner_id"),
            debit=Decimal(str(l.get("debit", 0))),
            credit=Decimal(str(l.get("credit", 0))),
            currency_id=l.get("currency_id"),
            amount_currency=l.get("amount_currency"),
            fx_rate=l.get("fx_rate"),
            tax_base_amount=l.get("tax_base_amount"),
            analytic_tag_id=l.get("analytic_tag_id"),
            description=l.get("description", ""),
        ))

    audit_svc.log("acc_journal_entry", entry.id, "post", company_id=company_id)
    return entry


@action()
def post_sales_invoice(invoice_id: int) -> "AccSalesInvoice":
    """
    Post a draft Sales Invoice.

    Journal structure:
      DR  Accounts Receivable        invoice.total
      CR  Revenue (per line)         line.subtotal each
      CR  Tax Output (PPN)           invoice.charge_amt  (if any)
      DR  Sales Discount             invoice.discount_amt (if any)
      DR  COGS / HPP (per product)   qty × avg_cost
      CR  Inventory / Persediaan     qty × avg_cost  (self-balancing with COGS)
    """
    from app.erp.erp_acc.models.invoice import AccSalesInvoice
    from app.erp.erp_stock.services.stock_compute import compute_avg_cost
    from app.erp.erp_stock.services.coa_resolver import (
        resolve_revenue_account, resolve_cogs_account, resolve_stock_account,
    )

    inv = AccSalesInvoice.query.get_or_404(invoice_id)
    if inv.journal_entry_id:
        raise ValueError(f"Invoice {inv.name} already has a journal entry")
    if inv.state == "cancelled":
        raise ValueError(f"Invoice {inv.name} is cancelled")

    company_id = inv.company_id

    lines = []
    computed_subtotal = Decimal("0")

    # ── Revenue + COGS per line ───────────────────────────────────────────────
    for il in inv.lines:
        product  = il.product
        subtotal = Decimal(str(il.subtotal or 0))
        if subtotal == 0:
            continue

        computed_subtotal += subtotal
        rev_acc = (
            getattr(il, "account_id", None)
            or (resolve_revenue_account(product, company_id) if product else None)
            or get_default_account(company_id, "income_default")
        )
        lines.append({
            "account_id": rev_acc, "debit": 0, "credit": float(subtotal),
            "description": getattr(il, "description", "") or "",
        })

        # COGS / HPP for storable products
        if product and not getattr(product, "is_stock_item", True) and product.bundle_components:
            # Bundle: post COGS for each component
            qty = Decimal(str(il.qty or 0))
            for comp in product.bundle_components:
                comp_product = comp.component
                if not comp_product or not getattr(comp_product, "is_stock_item", True):
                    continue
                acc_cogs  = resolve_cogs_account(comp_product, company_id)
                acc_stock = resolve_stock_account(comp_product, company_id)
                if not acc_cogs or not acc_stock:
                    continue
                comp_qty = qty * Decimal(str(comp.qty))
                cost     = Decimal(str(compute_avg_cost(comp_product.id, company_id=company_id)))
                amount   = round(comp_qty * cost, 2)
                if amount > 0:
                    lines.append({"account_id": acc_cogs,  "debit": float(amount), "credit": 0,
                                  "description": f"HPP {comp_product.name}"})
                    lines.append({"account_id": acc_stock, "debit": 0, "credit": float(amount),
                                  "description": f"Persediaan keluar {comp_product.name}"})
        elif product and getattr(product, "is_stock_item", True):
            acc_cogs  = resolve_cogs_account(product, company_id)
            acc_stock = resolve_stock_account(product, company_id)
            if acc_cogs and acc_stock:
                cost   = Decimal(str(compute_avg_cost(product.id, company_id=company_id)))
                qty    = Decimal(str(il.qty or 0))
                amount = round(qty * cost, 2)
                if amount > 0:
                    lines.append({"account_id": acc_cogs,  "debit": float(amount), "credit": 0,
                                  "description": f"HPP {product.name}"})
                    lines.append({"account_id": acc_stock, "debit": 0, "credit": float(amount),
                                  "description": f"Persediaan keluar {product.name}"})

    # ── Tax / PPN output (exclusive only) ────────────────────────────────────
    # Inclusive tax is already inside line subtotals — no extra CR needed.
    # Only post a PPN line when charge_amt > 0 (exclusive tax added on top).
    charge_amt = Decimal(str(inv.charge_amt or 0))
    posted_charge = Decimal("0")
    if charge_amt > 0:
        try:
            tax_acc = get_default_account(company_id, "tax_output_ppn")
            lines.append({"account_id": tax_acc, "debit": 0, "credit": float(charge_amt),
                          "description": "PPN Keluaran"})
            posted_charge = charge_amt
        except ValueError:
            pass

    # ── Sales discount (DR) ──────────────────────────────────────────────────
    discount_amt = Decimal(str(inv.discount_amt or 0))
    posted_discount = Decimal("0")
    if discount_amt > 0:
        try:
            disc_acc = get_default_account(company_id, "payment_discount")
            lines.append({"account_id": disc_acc, "debit": float(discount_amt), "credit": 0,
                          "description": "Diskon penjualan"})
            posted_discount = discount_amt
        except ValueError:
            pass  # no discount account — exclude discount from AR total too

    # ── Accounts Receivable (DR) — always derived from actual line subtotals ──
    total  = computed_subtotal + posted_charge - posted_discount
    inv.subtotal = float(computed_subtotal)
    inv.total    = float(total)
    ar_acc = get_default_account(company_id, "receivable_default")
    lines.append({"account_id": ar_acc, "debit": float(total), "credit": 0,
                  "partner_type": "customer", "partner_id": inv.customer_id,
                  "description": f"Piutang {inv.name}"})

    entry = post_journal(
        company_id=company_id,
        date=inv.invoice_date or date_type.today(),
        lines=lines,
        reference=inv.name,
        narrative=f"Sales Invoice {inv.name}",
        origin=("acc_sales_invoice", inv.id),
    )
    inv.journal_entry_id = entry.id

    # ── Stock movement (delivery) ─────────────────────────────────────────────
    location_id = getattr(inv, "location_id", None)
    if location_id:
        _post_sales_delivery(inv, company_id, location_id)

    inv.state = "posted"
    _upsert_sales_prices(inv)
    db.session.commit()
    return inv


def _upsert_sales_prices(inv):
    """Auto-save sales prices to StockPriceList if no price exists for product."""
    from app.erp.erp_stock.models.product import StockPriceList
    price_type_id = getattr(inv, "price_type_id", None)
    if not price_type_id:
        return
    for il in inv.lines:
        if not il.product_id or not getattr(il, "unit_price", None):
            continue
        existing = StockPriceList.find(
            product_id=il.product_id,
            price_type_id=price_type_id,
        )
        if existing:
            continue
        db.session.add(StockPriceList(
            product_id=il.product_id,
            price_type_id=price_type_id,
            currency_id=inv.currency_id,
            uom_id=getattr(il, "uom_id", None),
            price=il.unit_price,
            is_active=True,
        ))


def _post_sales_delivery(inv, company_id: int, location_id: int):
    from app.erp.erp_stock.models.movement import StockMovement, StockMovementLine
    from app.erp.erp_stock.models.warehouse import StockLocation
    from app.erp.erp_stock.services.posting import post_movement
    from app.erp.erp_main.models.doc_series import DocSeries as Sequence
    from app.erp.erp_main.services import sequence as seq_svc

    src_loc = StockLocation.get(location_id)
    if not src_loc:
        return

    seq = (Sequence.find(code="stock.delivery", company_id=company_id)
           or Sequence.find(code="stock.move", company_id=company_id))
    name = seq_svc.next_number_for_seq(seq) if seq else f"DEL/{company_id}/{inv.name}"

    mv = StockMovement(
        company_id=company_id,
        name=name,
        move_type="delivery",
        date_move=inv.invoice_date or date_type.today(),
        src_location_id=src_loc.id,
        state="confirmed",
        origin_model="acc_sales_invoice",
        origin_id=inv.id,
    )
    db.session.add(mv)
    db.session.flush()

    from app.erp.erp_stock.services.uom import to_base_qty
    from app.erp.erp_stock.services.stock_compute import compute_avg_cost

    for il in inv.lines:
        product = il.product
        if not product:
            continue
        qty = Decimal(str(il.qty or 0))
        if qty <= 0:
            continue

        if not getattr(product, "is_stock_item", True) and product.bundle_components:
            # Bundle: expand components into stock lines
            for comp in product.bundle_components:
                comp_product = comp.component
                if not comp_product or not getattr(comp_product, "is_stock_item", True):
                    continue
                comp_qty    = qty * Decimal(str(comp.qty))
                comp_uom_id = comp.uom_id or comp_product.uom_id
                comp_base   = to_base_qty(comp_product.id, comp_qty, comp_uom_id, comp_product.uom_id)
                cost        = compute_avg_cost(comp_product.id, company_id=company_id)
                db.session.add(StockMovementLine(
                    movement_id=mv.id,
                    product_id=comp_product.id,
                    uom_id=comp_uom_id,
                    qty=comp_qty,
                    qty_base=comp_base,
                    unit_cost=cost,
                    total_cost=comp_base * cost,
                ))
        elif getattr(product, "is_stock_item", True):
            uom_id   = il.uom_id or product.uom_id
            qty_base = to_base_qty(product.id, qty, uom_id, product.uom_id)
            cost     = compute_avg_cost(product.id, company_id=company_id)
            db.session.add(StockMovementLine(
                movement_id=mv.id,
                product_id=product.id,
                uom_id=uom_id,
                qty=qty,
                qty_base=qty_base,
                unit_cost=cost,
                total_cost=qty_base * cost,
            ))
    db.session.flush()
    post_movement(mv.id, skip_journal=True)  # journal already posted above


def reverse_entry(entry_id: int, date: date_type, narrative: str = "") -> AccJournalEntry:
    """Create a mirror entry with debit/credit swapped."""
    orig = AccJournalEntry.get(entry_id)
    if not orig or orig.state != "posted":
        raise ValueError("Can only reverse a posted entry")

    rev_lines = [
        {
            "account_id":      l.account_id,
            "debit":           l.credit,
            "credit":          l.debit,
            "partner_type":    l.partner_type,
            "partner_id":      l.partner_id,
            "currency_id":     l.currency_id,
            "amount_currency": (-l.amount_currency) if l.amount_currency else None,
            "fx_rate":         l.fx_rate,
            "tax_base_amount": l.tax_base_amount,
            "analytic_tag_id": l.analytic_tag_id,
            "description":     f"REV: {l.description or ''}",
        }
        for l in orig.lines
    ]

    return post_journal(
        company_id=orig.company_id,
        date=date,
        lines=rev_lines,
        reference=f"REV:{orig.name}",
        narrative=narrative or f"Reversal of {orig.name}",
        origin=("acc_journal_entry", orig.id),
    )


def _merge_lines(lines: list) -> list:
    """
    Merge journal lines with the same account_id into one row.
    Non-numeric metadata (description, partner_type, partner_id, etc.) is kept
    from the first line that carries it; amounts are summed.
    """
    merged: dict = {}
    order:  list = []
    for l in lines:
        acc = l["account_id"]
        if acc not in merged:
            merged[acc] = {
                "account_id":      acc,
                "debit":           Decimal("0"),
                "credit":          Decimal("0"),
                "partner_type":    l.get("partner_type", "none"),
                "partner_id":      l.get("partner_id"),
                "currency_id":     l.get("currency_id"),
                "amount_currency": l.get("amount_currency"),
                "fx_rate":         l.get("fx_rate"),
                "tax_base_amount": l.get("tax_base_amount"),
                "analytic_tag_id": l.get("analytic_tag_id"),
                "description":     l.get("description", ""),
            }
            order.append(acc)
        merged[acc]["debit"]  += Decimal(str(l.get("debit",  0)))
        merged[acc]["credit"] += Decimal(str(l.get("credit", 0)))
        # keep first non-empty description / partner
        if not merged[acc]["description"] and l.get("description"):
            merged[acc]["description"] = l["description"]
        if merged[acc]["partner_type"] == "none" and l.get("partner_type", "none") != "none":
            merged[acc]["partner_type"] = l["partner_type"]
            merged[acc]["partner_id"]   = l.get("partner_id")

    return [merged[acc] for acc in order]


def get_default_account(company_id: int, key: str) -> int:
    """Resolve a default account ID from Company fields (e.g. key='cash_default' → acc_cash_default_id)."""
    from app.erp.erp_config.models.company import Company
    from app.erp.erp_acc.models.account import AccAccount
    company = Company.get(company_id)
    if not company:
        raise ValueError(f"Company {company_id} not found")
    field = f"acc_{key}_id"
    acc_id = getattr(company, field, None)
    if not acc_id or not AccAccount.exists(id=acc_id):
        raise ValueError(f"Default account '{key}' not configured or missing in COA for company {company_id}")
    return acc_id


def _resolve_period(company_id: int, d: date_type):
    from app.erp.erp_main.models.fiscal import FiscalYear
    return (
        FiscalPeriod.query
        .join(FiscalYear, FiscalYear.id == FiscalPeriod.fiscal_year_id)
        .filter(
            FiscalYear.company_id == company_id,
            FiscalPeriod.date_start <= d,
            FiscalPeriod.date_end >= d,
        )
        .first()
    )
