from decimal import Decimal
from datetime import datetime
from arasCore.lib.extensions import db
from aras.app_erp.erp_pos.models import PosOrder, PosOrderLine, PosPayment, PosSession
from aras.app_erp.erp_core.services import sequence as seq_svc
from aras.app_erp.erp_stock.services.uom_service import to_base_qty
from aras.app_erp.erp_stock.services.price_service import get_price


def open_session(terminal_id: int, cashier_id: int, opening_balance: Decimal = Decimal(0)) -> PosSession:
    existing = PosSession.query.filter_by(terminal_id=terminal_id, state="open").first()
    if existing:
        return existing

    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    terminal = PosTerminal.query.get(terminal_id)
    company_id = terminal.company_id if terminal else None

    shift_number = None
    if company_id:
        try:
            shift_number = seq_svc.next_number("pos.shift", company_id)
        except ValueError:
            pass

    session = PosSession(
        terminal_id=terminal_id,
        cashier_id=cashier_id,
        opening_balance=opening_balance,
        shift_number=shift_number,
    )
    db.session.add(session)
    db.session.commit()
    return session


def close_session(session_id: int, cash_counted: Decimal, notes: str = "") -> PosSession:
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        raise ValueError("Session is not open")
    total_cash = sum(
        p.amount for o in session.orders.filter_by(state="paid")
        for p in o.payments.filter_by(method="cash")
    )
    session.closing_balance = session.opening_balance + total_cash
    session.cash_counted    = cash_counted
    session.cash_difference = cash_counted - session.closing_balance
    session.state           = "closed"
    session.closed_at       = datetime.utcnow()
    session.notes           = notes
    db.session.commit()
    return session


def create_order(session_id: int, cashier_id: int,
                 lines: list, customer_id: int = None, note: str = "") -> PosOrder:
    """
    lines: list of dicts — product_name, product_code, qty, unit_price,
           discount_pct, tax_id, tax_amt, note
    """
    session = PosSession.query.get_or_404(session_id)
    if session.state != "open":
        raise ValueError("Session is not open")

    from aras.app_erp.erp_pos.models.terminal import PosTerminal
    terminal = PosTerminal.query.get(session.terminal_id)
    company_id = terminal.company_id if terminal else None

    name = seq_svc.next_number("pos.order", company_id) if company_id else f"POS-{session_id}"

    subtotal = Decimal(0)
    tax_total = Decimal(0)
    pricelist_id = terminal.pricelist_id if terminal else None

    order_lines = []
    for l in lines:
        product_id = l.get("product_id")
        uom_id     = l.get("uom_id")
        qty        = Decimal(str(l.get("qty", 1)))
        disc_pct   = Decimal(str(l.get("discount_pct", 0)))
        tax_amt    = Decimal(str(l.get("tax_amt", 0)))

        # Auto-lookup price from pricelist if not provided
        if l.get("unit_price") is not None:
            price = Decimal(str(l["unit_price"]))
        elif product_id and uom_id:
            price = get_price(product_id, uom_id, qty, pricelist_id)
        else:
            price = Decimal("0")

        # Compute base UoM qty for stock posting
        qty_base = qty
        if product_id and uom_id:
            from aras.app_erp.erp_stock.models.product import StockProduct
            prod = StockProduct.query.get(product_id)
            if prod and prod.uom_id and uom_id != prod.uom_id:
                qty_base = to_base_qty(product_id, qty, uom_id, prod.uom_id)

        line_sub   = qty * price * (1 - disc_pct / 100)
        subtotal  += line_sub
        tax_total += tax_amt
        order_lines.append(PosOrderLine(
            product_id=product_id,
            product_name=l["product_name"],
            product_code=l.get("product_code"),
            uom_id=uom_id,
            qty=qty,
            qty_base=qty_base,
            unit_price=price,
            discount_pct=disc_pct,
            tax_id=l.get("tax_id"),
            tax_amt=tax_amt,
            subtotal=line_sub,
            note=l.get("note"),
        ))

    order = PosOrder(
        session_id=session_id,
        name=name,
        cashier_id=cashier_id,
        customer_id=customer_id,
        subtotal=subtotal,
        tax_amt=tax_total,
        total=subtotal + tax_total,
        note=note,
    )
    db.session.add(order)
    db.session.flush()
    for line in order_lines:
        line.order_id = order.id
        db.session.add(line)
    db.session.commit()
    return order


def pay_order(order_id: int, payments: list, tx_mode: str = "income") -> PosOrder:
    """
    payments: list of dicts — method, amount, reference
    tx_mode: "income" (sales) | "outcome" (purchase/receive) | "both"
    """
    order = PosOrder.query.get_or_404(order_id)
    if order.state != "draft":
        raise ValueError("Order already processed")

    total_paid = Decimal(0)
    for p in payments:
        amt = Decimal(str(p["amount"]))
        total_paid += amt
        db.session.add(PosPayment(
            order_id=order.id,
            method=p["method"],
            amount=amt,
            reference=p.get("reference"),
        ))

    order.amount_paid = total_paid
    order.change_amt  = max(Decimal(0), total_paid - order.total)
    order.state       = "paid"
    db.session.flush()

    from aras.app_erp.erp_pos.services.pos_invoice import (
        create_invoice_from_pos, create_purchase_invoice_from_pos,
    )
    from aras.app_erp.erp_pos.services.pos_stock import deduct_stock_from_order, receive_stock_from_order
    if tx_mode in ("income", "both"):
        create_invoice_from_pos(order.id)
        deduct_stock_from_order(order.id)
    elif tx_mode == "outcome":
        create_purchase_invoice_from_pos(order.id)
        receive_stock_from_order(order.id)

    db.session.commit()
    return order
