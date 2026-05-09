from arasCore.lib.core.extensions import db
from app.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation
from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice
from app.erp.erp_acc.services.posting import post_journal, get_default_account
from app.erp.erp_main.services import sequence as seq_svc
from arasCore.lib.core.action import action


@action()
def post_payment(payment_id: int) -> AccPayment:
    """Post draft payment — creates journal entry (AR/AP ↔ cash/bank)."""
    payment = AccPayment.get_or_404(payment_id)
    if payment.state != "draft":
        raise ValueError(f"Payment {payment.name} is already {payment.state}.")

    company_id = payment.company_id
    amount = float(payment.total_amount)

    if payment.payment_type == "inbound":
        cash_acc = _resolve_payment_account(payment)
        ar_acc   = get_default_account(company_id, "receivable_default")
        lines = [
            {"account_id": cash_acc, "debit": amount, "credit": 0,
             "partner_type": "customer", "partner_id": payment.partner_id,
             "description": payment.name},
            {"account_id": ar_acc,   "debit": 0, "credit": amount,
             "partner_type": "customer", "partner_id": payment.partner_id,
             "description": payment.name},
        ]
    else:
        cash_acc = _resolve_payment_account(payment)
        ap_acc   = get_default_account(company_id, "payable_default")
        lines = [
            {"account_id": ap_acc,   "debit": amount, "credit": 0,
             "partner_type": "vendor", "partner_id": payment.partner_id,
             "description": payment.name},
            {"account_id": cash_acc, "debit": 0, "credit": amount,
             "partner_type": "vendor", "partner_id": payment.partner_id,
             "description": payment.name},
        ]

    entry = post_journal(
        company_id=company_id,
        date=payment.payment_date,
        lines=lines,
        reference=payment.reference or payment.name,
        narrative=f"Payment {payment.name}",
        origin=("acc_payment", payment.id),
        sequence_code="accounting.payment",
    )

    payment.journal_entry_id = entry.id
    payment.state = "posted"
    db.session.commit()
    return payment


def get_unpaid_invoices(payment: AccPayment) -> list[dict]:
    """Return unpaid/partial invoices for the payment's partner, ordered oldest first."""
    # Use partner_type to decide which table to search; it's more reliable than payment_type
    if payment.partner_type == "customer":
        is_sales = True
    elif payment.partner_type == "supplier":
        is_sales = False
    else:
        # Fallback to payment_type if partner_type is 'other' or unknown
        is_sales = (payment.payment_type == "inbound")

    if is_sales:
        rows = AccSalesInvoice.query.filter(
            AccSalesInvoice.customer_id == payment.partner_id,
            AccSalesInvoice.state.in_(["posted", "partial"]),
        ).order_by(AccSalesInvoice.id).all()
        return [
            {
                "invoice_type": "sales",
                "invoice_id":   r.id,
                "name":         r.name,
                "total":        float(r.total),
                "amount_due":   float(r.amount_due),
            }
            for r in rows
        ]
    else:
        rows = AccPurchaseInvoice.query.filter(
            AccPurchaseInvoice.supplier_id == payment.partner_id,
            AccPurchaseInvoice.state.in_(["posted", "partial"]),
        ).order_by(AccPurchaseInvoice.id).all()
        return [
            {
                "invoice_type": "purchase",
                "invoice_id":   r.id,
                "name":         r.name,
                "total":        float(r.total),
                "amount_due":   float(r.amount_due),
            }
            for r in rows
        ]


@action()
def auto_allocate(payment_id: int) -> list[AccPaymentAllocation]:
    """
    Auto-allocate posted payment to unpaid invoices FIFO by amount.
    Returns list of created allocations.
    """
    payment = AccPayment.get_or_404(payment_id)
    if payment.state == "cancelled":
        raise ValueError("Cannot auto-allocate a cancelled payment.")

    invoices = get_unpaid_invoices(payment)
    remaining = payment.unallocated_amount
    created = []

    for inv in invoices:
        if remaining <= 0.001:
            break
        alloc_amt = min(remaining, inv["amount_due"])
        if alloc_amt <= 0:
            continue
        alloc = _do_allocate(payment, inv["invoice_type"], inv["invoice_id"], alloc_amt)
        created.append(alloc)
        remaining = payment.unallocated_amount

    db.session.commit()
    return created


@action()
def allocate(payment_id: int, invoice_type: str, invoice_id: int, amount: float) -> AccPaymentAllocation:
    """Allocate amount from payment to one invoice. Draft payments can pre-allocate."""
    payment = AccPayment.get_or_404(payment_id)
    if payment.state == "cancelled":
        raise ValueError("Cannot allocate a cancelled payment.")

    amount = float(amount)
    if amount <= 0:
        raise ValueError("Allocation amount must be positive.")
    if amount > payment.unallocated_amount + 0.001:
        raise ValueError(
            f"Allocation {amount} exceeds unallocated balance {payment.unallocated_amount:.4f}."
        )

    alloc = _do_allocate(payment, invoice_type, invoice_id, amount)
    db.session.commit()
    return alloc


def _do_allocate(payment: AccPayment, invoice_type: str, invoice_id: int, amount: float) -> AccPaymentAllocation:
    """Internal — create allocation row and update invoice state. Does NOT commit."""
    inv = _get_invoice(invoice_type, invoice_id)
    if inv.state not in ("posted", "partial", "draft"):
        raise ValueError(f"Invoice {inv.name} is not in a payable state ({inv.state}).")

    alloc = AccPaymentAllocation(
        payment_id=payment.id,
        invoice_type=invoice_type,
        invoice_id=invoice_id,
        amount=amount,
    )
    db.session.add(alloc)
    payment.allocated_amount = float(payment.allocated_amount) + amount
    db.session.flush()

    if inv.state == "draft":
        return alloc

    new_paid = inv.amount_paid
    if new_paid >= float(inv.total) - 0.001:
        inv.state = "paid"
    elif new_paid > 0:
        inv.state = "partial"

    return alloc


@action()
def deallocate(allocation_id: int) -> None:
    """Remove an allocation and revert invoice state."""
    alloc = AccPaymentAllocation.get_or_404(allocation_id)
    payment = AccPayment.get_or_404(alloc.payment_id)
    inv = _get_invoice(alloc.invoice_type, alloc.invoice_id)

    amount = float(alloc.amount)
    payment.allocated_amount = max(0.0, float(payment.allocated_amount) - amount)
    db.session.delete(alloc)
    db.session.flush()

    if inv:
        new_paid = inv.amount_paid
        if new_paid <= 0:
            inv.state = "posted"
        else:
            inv.state = "partial"

    db.session.commit()


def _get_invoice(invoice_type: str, invoice_id: int):
    if invoice_type == "sales":
        return AccSalesInvoice.get_or_404(invoice_id)
    elif invoice_type == "purchase":
        return AccPurchaseInvoice.get_or_404(invoice_id)
    raise ValueError(f"Unknown invoice_type: {invoice_type}")


def _resolve_payment_account(payment: AccPayment) -> int:
    if payment.mode_of_payment_id:
        from app.erp.erp_main.models.payment_mode import CompanyPaymentAccount
        mop_acc = CompanyPaymentAccount.find(
            mode_of_payment_id=payment.mode_of_payment_id,
            company_id=payment.company_id,
        )
        if mop_acc and mop_acc.account_id:
            return mop_acc.account_id
    return get_default_account(payment.company_id, "cash_default")
