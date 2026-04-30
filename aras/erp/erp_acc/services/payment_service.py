from arasCore.lib.core.extensions import db
from aras.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation
from aras.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice
from aras.erp.erp_acc.services.posting import post_journal, get_default_account
from aras.erp.erp_core.services import sequence as seq_svc


def post_payment(payment_id: int) -> AccPayment:
    """Post draft payment — creates journal entry (AR/AP ↔ cash/bank)."""
    payment = AccPayment.get_or_404(payment_id)
    if payment.state != "draft":
        raise ValueError(f"Payment {payment.name} is already {payment.state}.")

    company_id = payment.company_id
    amount = float(payment.total_amount)

    if payment.payment_type == "inbound":
        # DR cash/bank, CR accounts receivable
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
        # DR accounts payable, CR cash/bank
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


def allocate(payment_id: int, invoice_type: str, invoice_id: int, amount: float) -> AccPaymentAllocation:
    """
    Allocate amount from payment to an invoice.
    invoice_type: "sales" or "purchase"
    """
    payment = AccPayment.get_or_404(payment_id)
    if payment.state != "posted":
        raise ValueError("Only posted payments can be allocated.")

    amount = float(amount)
    if amount <= 0:
        raise ValueError("Allocation amount must be positive.")
    if amount > payment.unallocated_amount + 0.001:
        raise ValueError(
            f"Allocation {amount} exceeds unallocated balance {payment.unallocated_amount:.4f}."
        )

    alloc = AccPaymentAllocation(payment_id=payment_id, amount=amount)

    if invoice_type == "sales":
        inv = AccSalesInvoice.get_or_404(invoice_id)
        alloc.sales_invoice_id = invoice_id
    elif invoice_type == "purchase":
        inv = AccPurchaseInvoice.get_or_404(invoice_id)
        alloc.purchase_invoice_id = invoice_id
    else:
        raise ValueError(f"Unknown invoice_type: {invoice_type}")

    if inv.state not in ("posted", "partial"):
        raise ValueError(f"Invoice {inv.name} is not in a payable state ({inv.state}).")

    db.session.add(alloc)

    # update payment allocated_amount
    payment.allocated_amount = float(payment.allocated_amount) + amount

    # update invoice state
    db.session.flush()
    new_paid = inv.amount_paid
    inv_total = float(inv.total)
    if new_paid >= inv_total - 0.001:
        inv.state = "paid"
    elif new_paid > 0:
        inv.state = "partial"

    db.session.commit()
    return alloc


def deallocate(allocation_id: int) -> None:
    """Remove an allocation and revert invoice state."""
    alloc = AccPaymentAllocation.get_or_404(allocation_id)
    payment = AccPayment.get_or_404(alloc.payment_id)

    amount = float(alloc.amount)
    payment.allocated_amount = max(0.0, float(payment.allocated_amount) - amount)

    inv = alloc.sales_invoice or alloc.purchase_invoice
    db.session.delete(alloc)
    db.session.flush()

    if inv:
        new_paid = inv.amount_paid
        if new_paid <= 0:
            inv.state = "posted"
        else:
            inv.state = "partial"

    db.session.commit()


def _resolve_payment_account(payment: AccPayment) -> int:
    """Resolve cash/bank account from ModeOfPayment or company default."""
    if payment.mode_of_payment_id:
        from aras.erp.erp_core.models.payment_mode import CompanyPaymentAccount
        mop_acc = CompanyPaymentAccount.find(
            mode_of_payment_id=payment.mode_of_payment_id,
            company_id=payment.company_id,
        )
        if mop_acc and mop_acc.account_id:
            return mop_acc.account_id
    return get_default_account(payment.company_id, "cash_default")
