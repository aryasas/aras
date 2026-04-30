"""pos_invoice — POS order → Sales Invoice / Purchase Invoice + Journal Entry."""
from decimal import Decimal
from datetime import date

from arasCore.lib.core.extensions import db
from aras.erp.erp_pos.models.order import PosOrder
from aras.erp.erp_acc.models.invoice import (
    AccSalesInvoice, AccSalesInvoiceLine,
    AccPurchaseInvoice, AccPurchaseInvoiceLine,
)
from aras.erp.erp_core.services import sequence as seq_svc
from aras.erp.erp_acc.services.posting import post_journal, get_default_account


def create_invoice_from_pos(order_id: int) -> AccSalesInvoice:
    """
    Buat Sales Invoice dari POS order yang sudah paid.
    Idempotent — jika invoice sudah ada (via pos_order_id), kembalikan yang existing.
    """
    order = PosOrder.get_or_404(order_id)

    existing = AccSalesInvoice.find(pos_order_id=order.id)
    if existing:
        return existing

    if order.state != "paid":
        raise ValueError(f"POS order {order.name} belum paid (state={order.state})")

    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_core.models.currency import Currency
    terminal   = PosTerminal.get(order.session.terminal_id)
    company_id = terminal.company_id
    currency   = Currency.find(code="IDR")

    customer_id = order.customer_id or _get_or_create_walkin_customer(company_id)

    if terminal and terminal.invoice_sequence_id:
        from aras.erp.erp_core.models.sequence import Sequence
        seq      = Sequence.get(terminal.invoice_sequence_id)
        inv_name = seq_svc.next_number_for_seq(seq) if seq else seq_svc.next_number("sales.invoice", company_id)
    else:
        inv_name = seq_svc.next_number("sales.invoice", company_id)

    inv = AccSalesInvoice(
        company_id=company_id,
        name=inv_name,
        customer_id=customer_id,
        invoice_date=date.today(),
        due_date=date.today(),
        currency_id=currency.id if currency else 1,
        subtotal=order.subtotal,
        discount_amt=order.discount_amt,
        charge_amt=order.tax_amt,
        total=order.total,
        state="posted",
        reference=order.name,
        notes=f"Dari POS {order.name}",
        pos_order_id=order.id,
    )
    db.session.add(inv)
    db.session.flush()

    income_acc_id = get_default_account(company_id, "income_default")
    for line in order.lines:
        product = getattr(line, "product", None)
        if product:
            from aras.erp.erp_stock.services.coa_resolver import resolve_revenue_account
            revenue_acc_id = resolve_revenue_account(product, company_id) or income_acc_id
        else:
            revenue_acc_id = income_acc_id

        db.session.add(AccSalesInvoiceLine(
            invoice_id=inv.id,
            sequence=0,
            product_id=line.product_id,
            description=line.product_name,
            qty=line.qty,
            unit_price=line.unit_price,
            discount_pct=line.discount_pct or Decimal("0"),
            subtotal=line.subtotal,
            account_id=revenue_acc_id,
        ))

    db.session.flush()
    _post_pos_journal(inv, order, company_id)
    order.state = "invoiced"
    db.session.flush()
    return inv


def _post_pos_journal(inv: AccSalesInvoice, order: PosOrder, company_id: int):
    """
    Journal for POS sales invoice (single entry):
      CR Revenue (subtotal) + CR Tax (charge_amt if any)
      DR each payment method account (cash, qris, bank, etc.)
      DR Accounts Receivable for any credit balance
      DR COGS / CR Stock (for storable products, per product category accounts)
    """
    from aras.erp.erp_stock.services.coa_resolver import resolve_revenue_account, resolve_cogs_account, resolve_stock_account
    from aras.erp.erp_stock.models import StockValuation

    income_id = get_default_account(company_id, "income_default")
    charge_amt = Decimal(str(inv.charge_amt or 0))
    tax_output_id = None
    if charge_amt > 0:
        try:
            tax_output_id = get_default_account(company_id, "tax_output_ppn")
        except ValueError:
            pass

    lines = []
    # Revenue lines — use NET subtotal (gross minus proportional tax if tax included in price)
    total_gross = sum(Decimal(str(il.subtotal or 0)) for il in inv.lines)
    total_revenue = Decimal("0")
    for il in inv.lines:
        product  = getattr(il, "product", None)
        rev_acc  = (resolve_revenue_account(product, company_id) if product else None) or income_id
        gross    = Decimal(str(il.subtotal or 0))
        # When tax is in charge_amt (inclusive), extract tax proportionally per line
        if charge_amt > 0 and total_gross > 0:
            line_tax = charge_amt * gross / total_gross
            net = gross - line_tax
        else:
            net = gross
        lines.append({"account_id": rev_acc, "debit": 0, "credit": float(net),
                      "description": f"Revenue {il.description or inv.name}"})
        total_revenue += net

    if tax_output_id and charge_amt > 0:
        lines.append({"account_id": tax_output_id, "debit": 0, "credit": float(charge_amt),
                      "description": "Tax output PPN"})

    payments    = order.payments.all() if hasattr(order.payments, "all") else list(order.payments)
    total_order = Decimal(str(inv.total))
    total_paid  = Decimal("0")

    for p in payments:
        amt = Decimal(str(p.amount))
        if p.method == "credit":
            # Explicit credit balance payment → AR
            try:
                ar_id = get_default_account(company_id, "receivable_default")
                lines.append({"account_id": ar_id, "debit": float(amt), "credit": 0,
                              "partner_type": "customer", "partner_id": inv.customer_id,
                              "description": f"AR credit {inv.name}"})
            except ValueError:
                pass
        else:
            acc_id = _payment_method_account(company_id, p.method)
            lines.append({"account_id": acc_id, "debit": float(amt), "credit": 0,
                          "description": f"POS {p.method} {inv.reference}"})
        total_paid += amt

    # Implicit credit balance (underpayment without explicit credit line)
    credit_balance = total_order - total_paid
    if credit_balance > Decimal("0.001"):
        try:
            ar_id = get_default_account(company_id, "receivable_default")
            lines.append({"account_id": ar_id, "debit": float(credit_balance), "credit": 0,
                          "partner_type": "customer", "partner_id": inv.customer_id,
                          "description": f"AR credit balance {inv.name}"})
        except ValueError:
            kas_id = get_default_account(company_id, "cash_default")
            lines.append({"account_id": kas_id, "debit": float(credit_balance), "credit": 0,
                          "description": f"POS credit (no AR) {inv.name}"})

    if not payments and credit_balance <= Decimal("0.001"):
        kas_id = get_default_account(company_id, "cash_default")
        lines.append({"account_id": kas_id, "debit": float(total_order), "credit": 0,
                      "description": f"POS kas {inv.reference}"})

    # COGS lines — DR COGS / CR Stock, resolved per product → category → company default
    for ol in order.lines:
        product = getattr(ol, "product", None)
        if not product or not getattr(product, "is_stock_item", True):
            continue
        acc_cogs  = resolve_cogs_account(product, company_id)
        acc_stock = resolve_stock_account(product, company_id)
        if not acc_cogs or not acc_stock:
            continue
        val = StockValuation.find(product_id=product.id, company_id=company_id)
        cost = Decimal(str(val.avg_cost if val else 0))
        qty  = Decimal(str(ol.qty_base or ol.qty))
        amount = qty * cost
        if amount <= 0:
            continue
        lines.append({"account_id": acc_cogs,  "debit": float(amount), "credit": 0,
                      "description": f"HPP {product.name}"})
        lines.append({"account_id": acc_stock, "debit": 0, "credit": float(amount),
                      "description": f"Stock out {product.name}"})

    entry = post_journal(
        company_id=company_id,
        date=date.today(),
        lines=lines,
        reference=inv.name,
        narrative=f"POS {order.name}",
        origin=("acc_sales_invoice", inv.id),
    )
    inv.journal_entry_id = entry.id

    # Record payment rows in AccInvoicePayment + update invoice state
    _record_invoice_payments(inv, order, payments, total_paid, total_order)


def _payment_method_account(company_id: int, method: str) -> int:
    """Resolve GL account for a payment method via ModeOfPayment → CompanyPaymentAccount, then company defaults."""
    from aras.erp.erp_core.models.payment_mode import ModeOfPayment, CompanyPaymentAccount
    mop = ModeOfPayment.find(name=method) or ModeOfPayment.find(payment_type=method)
    if mop:
        cpa = CompanyPaymentAccount.find(mode_of_payment_id=mop.id, company_id=company_id)
        if cpa and cpa.account_id:
            return cpa.account_id
    from aras.erp.erp_core.models.company import Company
    company = Company.get(company_id)
    key_map = {"cash": "cash_default", "card": "bank_default", "qris": "bank_default", "transfer": "bank_default"}
    field   = f"acc_{key_map.get(method, 'cash_default')}_id"
    acc_id  = getattr(company, field, None) if company else None
    return acc_id or get_default_account(company_id, "cash_default")


def _record_invoice_payments(inv: AccSalesInvoice, order: PosOrder,
                              payments: list, total_paid: Decimal, total_order: Decimal):
    """Create AccPayment + AccPaymentAllocation rows for each POS payment split."""
    from aras.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation
    from aras.erp.erp_core.models.currency import Currency
    for p in payments:
        pay = AccPayment(
            company_id   = inv.company_id,
            name         = f"POS-{order.name}-{p.method}",
            payment_type = "inbound",
            partner_type = "customer",
            partner_id   = inv.customer_id,
            payment_date = date.today(),
            method       = p.method,
            total_amount = p.amount,
            allocated_amount = p.amount,
            state        = "posted",
            reference    = order.name,
        )
        db.session.add(pay)
        db.session.flush()
        db.session.add(AccPaymentAllocation(
            payment_id       = pay.id,
            sales_invoice_id = inv.id,
            amount           = p.amount,
        ))

    # Credit method = AR balance (not yet paid) — don't count toward cash paid
    cash_paid = sum(Decimal(str(p.amount)) for p in payments if p.method != "credit")
    if cash_paid >= total_order - Decimal("0.01"):
        inv.state = "paid"
    elif cash_paid > 0 or total_paid > 0:
        inv.state = "partial"
    else:
        inv.state = "posted"


def _get_or_create_walkin_customer(company_id: int) -> int:
    from aras.erp.erp_crm.models.customer import CrmCustomer
    from aras.erp.erp_core.models.currency import Currency
    cur = Currency.find(code="IDR")
    c, _ = CrmCustomer.get_or_create(
        {"name": "Walk-in Customer", "type": "individual", "currency_id": cur.id if cur else None},
        company_id=company_id, code="WALKIN",
    )
    return c.id


# ── Purchase Invoice (outcome mode) ──────────────────────────────────────────

def create_purchase_invoice_from_pos(order_id: int) -> AccPurchaseInvoice:
    """
    Create a Purchase Invoice (Bill) from a POS outcome order.
    Idempotent — returns existing if already created.
    """
    order = PosOrder.get_or_404(order_id)

    existing = AccPurchaseInvoice.find(pos_order_id=order.id)
    if existing:
        return existing

    if order.state != "paid":
        raise ValueError(f"POS order {order.name} not paid (state={order.state})")

    from aras.erp.erp_pos.models.terminal import PosTerminal
    from aras.erp.erp_core.models.currency import Currency
    terminal   = PosTerminal.get(order.session.terminal_id)
    company_id = terminal.company_id
    currency   = Currency.find(code="IDR")

    bill_name = seq_svc.next_number("purchase.invoice", company_id)

    bill = AccPurchaseInvoice(
        company_id=company_id,
        name=bill_name,
        invoice_date=date.today(),
        due_date=date.today(),
        currency_id=currency.id if currency else 1,
        subtotal=order.subtotal,
        discount_amt=order.discount_amt,
        charge_amt=order.tax_amt,
        total=order.total,
        state="posted",
        notes=f"From POS {order.name}",
        pos_order_id=order.id,
    )
    db.session.add(bill)
    db.session.flush()

    purchase_acc_id = get_default_account(company_id, "payable_default")
    for line in order.lines:
        product = getattr(line, "product", None)
        if product:
            from aras.erp.erp_stock.services.coa_resolver import resolve_purchase_account
            acc_id = resolve_purchase_account(product, company_id) or purchase_acc_id
        else:
            acc_id = purchase_acc_id

        db.session.add(AccPurchaseInvoiceLine(
            invoice_id=bill.id,
            sequence=0,
            product_id=line.product_id,
            description=line.product_name,
            qty=line.qty,
            uom_id=line.uom_id,
            unit_price=line.unit_price,
            discount_pct=line.discount_pct or Decimal("0"),
            subtotal=line.subtotal,
            account_id=acc_id,
        ))

    db.session.flush()
    _post_purchase_journal(bill, order, company_id)
    order.state = "invoiced"
    db.session.flush()
    return bill


def _post_purchase_journal(bill: AccPurchaseInvoice, order: PosOrder, company_id: int):
    # COGS/expense debit — fall back to payable if cogs not configured
    try:
        expense_id = get_default_account(company_id, "cogs_default")
    except ValueError:
        expense_id = get_default_account(company_id, "payable_default")

    lines = [{"account_id": expense_id, "debit": float(bill.subtotal), "credit": 0,
               "description": f"Purchase {bill.name}"}]

    if float(bill.charge_amt) > 0:
        try:
            tax_in_id = get_default_account(company_id, "tax_input_ppn")
            lines.append({"account_id": tax_in_id, "debit": float(bill.charge_amt), "credit": 0,
                           "description": "PPN Masukan"})
        except ValueError:
            lines[0]["debit"] = float(bill.total)

    payments = order.payments.all() if hasattr(order.payments, "all") else list(order.payments)
    total_order = float(bill.total)

    if payments:
        total_paid_raw = sum(float(p.amount) for p in payments)
        for i, p in enumerate(payments):
            share = round(float(p.amount) / total_paid_raw * total_order, 4) if total_paid_raw > 0 else (total_order if i == 0 else 0)
            acc_id = _payment_method_account(company_id, p.method)
            lines.append({"account_id": acc_id, "debit": 0, "credit": share,
                           "description": f"POS {p.method} {order.name}"})
        diff = round(sum(l["debit"] for l in lines) - sum(l["credit"] for l in lines), 4)
        if abs(diff) > 0:
            for l in reversed(lines):
                if l["credit"] > 0:
                    l["credit"] = round(l["credit"] + diff, 4)
                    break
    else:
        kas_id = get_default_account(company_id, "cash_default")
        lines.append({"account_id": kas_id, "debit": 0, "credit": total_order,
                       "description": f"POS cash {order.name}"})

    entry = post_journal(
        company_id=company_id,
        date=date.today(),
        lines=lines,
        reference=bill.name,
        narrative=f"POS purchase {order.name}",
        origin=("acc_purchase_invoice", bill.id),
    )
    bill.journal_entry_id = entry.id
