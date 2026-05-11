from decimal import Decimal
from datetime import datetime
from arasCore.lib.core.extensions import db
from app.erp.erp_pos.models import PosSession
from app.erp.erp_main.services import sequence as seq_svc
from app.erp.erp_stock.services.uom import to_base_qty
from app.erp.erp_stock.services.price import get_price


def open_session(terminal_id: int, cashier_id: int, opening_balance: Decimal = Decimal(0)) -> PosSession:
    existing = PosSession.query.filter_by(terminal_id=terminal_id, state="open").first()
    if existing:
        return existing
    from app.erp.erp_pos.models.terminal import PosTerminal
    terminal   = PosTerminal.query.get(terminal_id)
    company_id = terminal.company_id if terminal else None
    shift_number = None
    if company_id:
        try:
            shift_number = seq_svc.next_code(company_id, "pos.shift")
        except ValueError:
            pass
    session = PosSession(terminal_id=terminal_id, cashier_id=cashier_id,
                         opening_balance=opening_balance, shift_number=shift_number,
                         company_id=company_id)
    db.session.add(session)
    db.session.commit()
    return session


def close_session(session_id: int, cash_counted: Decimal, notes: str = "") -> PosSession:
    from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccPurchaseInvoice
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        raise ValueError("Session is not open")
    # Sum cash payments from actual invoices linked to this session
    cash_total = Decimal("0")
    for inv in AccSalesInvoice.find_all(pos_session_id=session_id):
        for alloc in inv.allocations:
            if alloc.payment and alloc.payment.method == "cash":
                cash_total += Decimal(str(alloc.amount))
    
    # Subtract cash payments for purchases (outcome mode)
    for bill in AccPurchaseInvoice.find_all(pos_session_id=session_id):
        for alloc in bill.allocations:
            if alloc.payment and alloc.payment.method == "cash":
                cash_total -= Decimal(str(alloc.amount))

    session.closing_balance = session.opening_balance + cash_total
    session.cash_counted    = cash_counted
    session.cash_difference = cash_counted - session.closing_balance
    session.state           = "closed"
    session.closed_at       = datetime.utcnow()
    session.notes           = notes
    db.session.commit()
    return session


def create_and_pay(session_id: int, cashier_id: int, lines: list,
                   payments: list, customer_id: int = None, supplier_id: int = None,
                   note: str = "", tx_mode: str = "income"):
    """
    Main POS submit: enrich lines, create draft invoice via standard posting pipeline.
    Returns the created AccSalesInvoice or AccPurchaseInvoice.
    """
    from app.erp.erp_pos.models.terminal import PosTerminal
    from app.erp.erp_stock.models.product import StockProduct

    session    = PosSession.query.get_or_404(session_id)
    terminal   = PosTerminal.get(session.terminal_id)
    company_id = terminal.company_id if terminal else None
    selling_pricelist_id  = terminal.selling_pricelist_id if terminal else None
    purchase_pricelist_id = terminal.purchase_pricelist_id if terminal else None
    pricelist_id = purchase_pricelist_id if tx_mode == 'outcome' else selling_pricelist_id

    # Enrich lines: fill price, uom, qty_base, subtotal
    enriched = []
    subtotal  = Decimal("0")
    tax_total = Decimal("0")
    for l in lines:
        pid  = l["product_id"]
        prod = StockProduct.get(pid)
        if not prod:
            raise ValueError(f"Product {pid} not found")
        uom_id = l.get("uom_id") or prod.uom_sales_id or prod.uom_id
        qty    = Decimal(str(l.get("qty", 1)))
        price  = Decimal(str(l["unit_price"])) if l.get("unit_price") is not None else get_price(pid, uom_id, qty, pricelist_id)
        disc   = Decimal(str(l.get("discount_pct", 0)))
        tax_amt= Decimal(str(l.get("tax_amt", 0)))
        gross  = qty * price * (1 - disc / 100)
        qty_base = qty
        if prod.uom_id and uom_id and uom_id != prod.uom_id:
            qty_base = to_base_qty(pid, qty, uom_id, prod.uom_id)
        subtotal  += gross
        tax_total += tax_amt
        enriched.append({**l, "product_name": prod.name, "product_code": prod.code,
                          "uom_id": uom_id, "qty": qty, "qty_base": qty_base,
                          "unit_price": price, "discount_pct": disc,
                          "tax_amt": tax_amt, "subtotal": gross})

    total      = subtotal  # inclusive tax already in subtotal
    total_paid = sum(Decimal(str(p["amount"])) for p in payments)
    change     = max(Decimal("0"), total_paid - total)

    if tx_mode in ("income", "both"):
        inv = _make_sales_invoice(session, terminal, enriched, payments,
                                   subtotal, tax_total, total, customer_id, note)
    else:
        inv = _make_purchase_invoice(session, terminal, enriched, payments,
                                      subtotal, tax_total, total, supplier_id, note)

    return inv, change


def _make_sales_invoice(session, terminal, lines, payments,
                         subtotal, tax_total, total, customer_id, note):
    from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine
    from app.erp.erp_acc.services.posting import post_sales_invoice, get_default_account
    from app.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation
    from app.erp.erp_config.models.currency import Currency
    from app.erp.erp_stock.services.coa_resolver import resolve_revenue_account
    from app.erp.erp_main.services import sequence as seq_svc

    company_id  = terminal.company_id
    currency    = Currency.find(code="IDR")
    customer_id = customer_id or _walkin_customer(company_id)
    inv_name    = _inv_name(terminal, company_id, "sales.invoice")

    inv = AccSalesInvoice(
        company_id    = company_id,
        name          = inv_name,
        customer_id   = customer_id,
        location_id   = terminal.location_id,
        pos_session_id= session.id,
        price_type_id = terminal.selling_pricelist_id,
        invoice_date  = __import__("datetime").date.today(),
        due_date      = __import__("datetime").date.today(),
        currency_id   = currency.id if currency else 1,
        subtotal      = subtotal,
        discount_amt  = Decimal("0"),
        charge_amt    = Decimal("0"),  # inclusive tax is inside subtotal, not extra
        total         = total,
        state         = "draft",
        reference     = session.shift_number or str(session.id),
        notes         = note,
    )
    db.session.add(inv)
    db.session.flush()

    for l in lines:
        from app.erp.erp_stock.models.product import StockProduct
        product = StockProduct.get(l["product_id"])
        rev_acc = resolve_revenue_account(product, company_id) if product else None
        if not rev_acc:
            rev_acc = get_default_account(company_id, "income_default")
        db.session.add(AccSalesInvoiceLine(
            invoice_id=inv.id, sequence=0,
            product_id=l["product_id"], description=l.get("product_name", ""),
            qty=l["qty"], uom_id=l.get("uom_id"),
            unit_price=l["unit_price"], discount_pct=l["discount_pct"],
            subtotal=l["subtotal"], account_id=rev_acc,
        ))

    # Record payments BEFORE posting invoice to trigger direct-payment journal entries
    from app.erp.erp_acc.services.payment import allocate
    from app.erp.erp_main.models.payment_mode import ModeOfPayment

    for p in payments:
        method_name = p.get("method", "cash")
        if method_name == 'credit':
            continue
            
        amt = Decimal(str(p["amount"]))
        if amt <= 0.001:
            continue

        mop = ModeOfPayment.query.filter(ModeOfPayment.name.ilike(method_name)).first()
        
        pay = AccPayment(
            company_id=company_id, name=f"POS-{inv.name}-{method_name}",
            payment_type="inbound", partner_type="customer", partner_id=customer_id,
            payment_date=__import__("datetime").date.today(),
            method=method_name, 
            mode_of_payment_id=mop.id if mop else None,
            total_amount=amt, 
            state="posted", # Mark as posted directly as its JE is handled by the invoice
        )
        db.session.add(pay)
        db.session.flush()
        
        # Allocate to invoice while it's still draft
        allocate(pay.id, "sales", inv.id, float(amt))
        
    db.session.flush()
    post_sales_invoice(inv.id)  # This now creates one JE with cash lines directly

    return inv


def _make_purchase_invoice(session, terminal, lines, payments,
                            subtotal, tax_total, total, supplier_id, note):
    from app.erp.erp_acc.models.invoice import AccPurchaseInvoice, AccPurchaseInvoiceLine
    from app.erp.erp_acc.services.purchase_posting import post_purchase_invoice
    from app.erp.erp_acc.services.posting import get_default_account
    from app.erp.erp_acc.models.payment import AccPayment, AccPaymentAllocation
    from app.erp.erp_config.models.currency import Currency
    from app.erp.erp_stock.services.coa_resolver import resolve_stock_account, resolve_purchase_account

    company_id = terminal.company_id
    currency   = Currency.find(code="IDR")
    bill_name  = _inv_name(terminal, company_id, "purchase.bill")

    bill = AccPurchaseInvoice(
        company_id    = company_id,
        name          = bill_name,
        supplier_id   = supplier_id,
        location_id   = terminal.location_id,
        pos_session_id= session.id,
        price_type_id = terminal.purchase_pricelist_id,
        invoice_date  = __import__("datetime").date.today(),
        due_date      = __import__("datetime").date.today(),
        currency_id   = currency.id if currency else 1,
        subtotal      = subtotal,
        discount_amt  = Decimal("0"),
        charge_amt    = tax_total,
        total         = total,
        state         = "draft",
        notes         = note,
    )
    db.session.add(bill)
    db.session.flush()

    payable_acc = get_default_account(company_id, "payable_default")
    for l in lines:
        from app.erp.erp_stock.models.product import StockProduct
        product = StockProduct.get(l["product_id"])
        if product and getattr(product, "is_stock_item", True):
            acc_id = resolve_stock_account(product, company_id)
        elif product:
            acc_id = resolve_purchase_account(product, company_id)
        else:
            acc_id = payable_acc
        db.session.add(AccPurchaseInvoiceLine(
            invoice_id=bill.id, sequence=0,
            product_id=l["product_id"], description=l.get("product_name", ""),
            qty=l["qty"], uom_id=l.get("uom_id"),
            unit_price=l["unit_price"], discount_pct=l["discount_pct"],
            subtotal=l["subtotal"], account_id=acc_id or payable_acc,
        ))

    # Record payments BEFORE posting
    from app.erp.erp_acc.services.payment import allocate
    from app.erp.erp_main.models.payment_mode import ModeOfPayment

    for p in payments:
        method_name = p.get("method", "cash")
        if method_name == 'credit':
            continue

        amt = Decimal(str(p["amount"]))
        if amt <= 0.001:
            continue

        mop = ModeOfPayment.query.filter(ModeOfPayment.name.ilike(method_name)).first()

        pay = AccPayment(
            company_id=company_id, name=f"POS-{bill.name}-{method_name}",
            payment_type="outbound", partner_type="supplier", partner_id=supplier_id,
            payment_date=__import__("datetime").date.today(),
            method=method_name, 
            mode_of_payment_id=mop.id if mop else None,
            total_amount=amt, 
            state="posted", # Handled by invoice JE
        )
        db.session.add(pay)
        db.session.flush()

        # Allocate to invoice while draft
        allocate(pay.id, "purchase", bill.id, float(amt))

    db.session.flush()
    post_purchase_invoice(bill.id)  # Creates one JE with credit to cash accounts directly

    return bill


def _inv_name(terminal, company_id: int, seq_key: str) -> str:
    if terminal and terminal.invoice_sequence_id:
        from app.erp.erp_main.models.doc_series import DocSeries as Sequence
        seq = Sequence.get(terminal.invoice_sequence_id)
        if seq:
            return seq_svc.next_number_for_seq(seq)
    return seq_svc.next_code(company_id, seq_key)


def _walkin_customer(company_id: int) -> int:
    from app.erp.erp_crm.models.customer import CrmCustomer
    from app.erp.erp_config.models.currency import Currency
    cur = Currency.find(code="IDR")
    c, _ = CrmCustomer.get_or_create(
        {"name": "Walk-in Customer", "type": "individual", "currency_id": cur.id if cur else None},
        company_id=company_id, code="WALKIN",
    )
    return c.id
