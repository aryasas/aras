"""pos_invoice — konversi POS order paid menjadi Sales Invoice + Journal Entry."""
from decimal import Decimal
from datetime import date

from arasCore.lib.extensions import db
from aras.app_erp.erp_pos.models.order import PosOrder
from aras.app_erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine
from aras.app_erp.erp_acc.models.journal import AccJournal
from aras.app_erp.erp_acc.models.account import AccDefaultAccount
from aras.app_erp.erp_core.services import sequence as seq_svc
from aras.app_erp.erp_acc.services.posting import post_journal


def create_invoice_from_pos(order_id: int) -> AccSalesInvoice:
    """
    Buat Sales Invoice dari POS order yang sudah paid.
    Juga post journal entry otomatis.
    Idempotent — jika invoice sudah ada (via pos_order_id), kembalikan yang existing.
    """
    order = PosOrder.query.get_or_404(order_id)

    existing = AccSalesInvoice.query.filter_by(pos_order_id=order.id).first()
    if existing:
        return existing

    if order.state != "paid":
        raise ValueError(f"POS order {order.name} belum paid (state={order.state})")

    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    terminal = PosTerminal.query.get(order.session.terminal_id)
    company_id = terminal.company_id

    # Resolusi: customer wajib ada untuk sales invoice; gunakan walk-in default jika kosong
    customer_id = order.customer_id
    if not customer_id:
        customer_id = _get_or_create_walkin_customer(company_id)

    # Currency default IDR
    from aras.app_erp.erp_core.models.currency import CoreCurrency
    currency = CoreCurrency.query.filter_by(code="IDR").first()

    journal = AccJournal.query.filter_by(company_id=company_id, code="SALES", is_active=True).first()

    inv_name = seq_svc.next_number("sales.invoice", company_id)

    inv = AccSalesInvoice(
        company_id=company_id,
        name=inv_name,
        customer_id=customer_id,
        invoice_date=date.today(),
        due_date=date.today(),
        currency_id=currency.id if currency else 1,
        journal_id=journal.id if journal else None,
        subtotal=order.subtotal,
        discount_amt=order.discount_amt,
        tax_amt=order.tax_amt,
        total=order.total,
        amount_paid=order.amount_paid,
        amount_due=max(Decimal("0"), order.total - order.amount_paid),
        state="posted",
        reference=order.name,
        notes=f"Dari POS {order.name}",
        pos_order_id=order.id,
    )
    db.session.add(inv)
    db.session.flush()

    # Lines
    income_acc_id = _default_account_id(company_id, "income_default")
    for line in order.lines:
        product = getattr(line, "product", None)
        if product:
            from aras.app_erp.erp_stock.services.coa_resolver import resolve_revenue_account
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
            tax_id=line.tax_id,
            tax_amt=line.tax_amt or Decimal("0"),
            subtotal=line.subtotal,
            account_id=revenue_acc_id,
        ))

    db.session.flush()

    # Journal Entry: Kas/Bank Dr, Pendapatan Cr
    _post_pos_journal(inv, order, company_id)

    order.state = "invoiced"
    db.session.flush()

    return inv


def _post_pos_journal(inv: AccSalesInvoice, order: PosOrder, company_id: int):
    income_id = _default_account_id(company_id, "income_default")
    tax_output_id = None
    if float(inv.tax_amt) > 0:
        try:
            tax_output_id = _default_account_id(company_id, "tax_output_ppn")
        except ValueError:
            pass

    # Sisi kredit
    lines = []
    credit_income = float(inv.subtotal)
    if tax_output_id and float(inv.tax_amt) > 0:
        lines.append({"account_id": income_id,    "debit": 0, "credit": credit_income, "description": f"Pendapatan {inv.name}"})
        lines.append({"account_id": tax_output_id,"debit": 0, "credit": float(inv.tax_amt), "description": "PPN Keluaran"})
    else:
        lines.append({"account_id": income_id,    "debit": 0, "credit": float(inv.total), "description": f"Pendapatan {inv.name}"})

    # Sisi debit: kas/bank masuk = order.total (bukan payment amount; kembalian bukan pendapatan)
    payments = order.payments.all() if hasattr(order.payments, "all") else list(order.payments)
    total_order = float(inv.total)

    if payments:
        # Distribusi per metode secara proporsional terhadap total order
        total_paid_raw = sum(float(p.amount) for p in payments)
        for i, p in enumerate(payments):
            if total_paid_raw > 0:
                share = round(float(p.amount) / total_paid_raw * total_order, 4)
            else:
                share = total_order if i == 0 else 0
            acc_id = _payment_method_account(company_id, p.method, _default_account_id(company_id, "suspense"))
            lines.append({
                "account_id": acc_id,
                "debit": share,
                "credit": 0,
                "description": f"POS {p.method} {inv.reference}",
            })
        # Koreksi rounding agar balance sempurna
        actual_debit = sum(l["debit"] for l in lines)
        actual_credit = sum(l["credit"] for l in lines)
        diff = round(actual_credit - actual_debit, 4)
        if abs(diff) > 0:
            for l in reversed(lines):
                if l["debit"] > 0:
                    l["debit"] = round(l["debit"] + diff, 4)
                    break
    else:
        kas_id = _default_account_id(company_id, "suspense")
        lines.append({"account_id": kas_id, "debit": total_order, "credit": 0, "description": f"POS kas {inv.reference}"})

    entry = post_journal(
        company_id=company_id,
        journal_code="CASH",
        date=date.today(),
        lines=lines,
        reference=inv.name,
        narrative=f"POS {order.name}",
        origin=("acc_sales_invoice", inv.id),
    )
    inv.journal_entry_id = entry.id


def _default_account_id(company_id: int, key: str) -> int:
    row = AccDefaultAccount.query.filter_by(company_id=company_id, key=key).first()
    if not row:
        raise ValueError(f"Default account '{key}' belum dikonfigurasi untuk company {company_id}")
    return row.account_id


def _payment_method_account(company_id: int, method: str, fallback_id: int) -> int:
    """Petakan metode pembayaran POS ke akun GL."""
    key_map = {
        "cash":     "cash_default",
        "card":     "bank_card_default",
        "qris":     "bank_card_default",
        "transfer": "bank_transfer_default",
    }
    key = key_map.get(method)
    if key:
        row = AccDefaultAccount.query.filter_by(company_id=company_id, key=key).first()
        if row:
            return row.account_id
    # fallback ke kas besar
    row = AccDefaultAccount.query.filter_by(company_id=company_id, key="suspense").first()
    return row.account_id if row else fallback_id


def _get_or_create_walkin_customer(company_id: int) -> int:
    from aras.app_erp.erp_crm.models.customer import CrmCustomer
    c = CrmCustomer.query.filter_by(company_id=company_id, code="WALKIN").first()
    if not c:
        from aras.app_erp.erp_core.models.currency import CoreCurrency
        cur = CoreCurrency.query.filter_by(code="IDR").first()
        c = CrmCustomer(
            company_id=company_id,
            code="WALKIN",
            name="Walk-in Customer",
            type="individual",
            currency_id=cur.id if cur else None,
        )
        db.session.add(c)
        db.session.flush()
    return c.id
