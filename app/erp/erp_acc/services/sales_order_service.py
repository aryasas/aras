from arasCore.lib.core.extensions import db
from app.erp.erp_acc.models.sales_order import SalesOrder, SalesOrderLine, SalesOrderCharge
from app.erp.erp_acc.models.invoice import AccSalesInvoice, AccSalesInvoiceLine, AccSalesInvoiceCharge
from app.erp.erp_core.services import sequence as seq_svc


def confirm_order(order_id: int) -> SalesOrder:
    order = SalesOrder.get_or_404(order_id)
    if order.state != "draft":
        raise ValueError(f"Order {order.name} is already {order.state}.")
    order.state = "confirmed"
    db.session.commit()
    return order


def create_invoice_from_order(order_id: int) -> AccSalesInvoice:
    """Create a Sales Invoice from a confirmed Sales Order."""
    order = SalesOrder.get_or_404(order_id)
    if order.state not in ("confirmed", "partial"):
        raise ValueError(f"Order {order.name} must be confirmed before invoicing.")

    inv_name = seq_svc.next_code(order.company_id, "accounting.sales_invoice")

    inv = AccSalesInvoice(
        company_id      = order.company_id,
        name            = inv_name,
        customer_id     = order.customer_id,
        location_id     = order.location_id,
        origin_order_id = order.id,
        invoice_date    = db.func.current_date(),
        currency_id     = order.currency_id,
        price_type_id   = order.price_type_id,
        subtotal        = order.subtotal,
        discount_amt    = order.discount_amt,
        charge_amt      = order.charge_amt,
        total           = order.total,
        payment_term_days = order.payment_term_days if hasattr(order, "payment_term_days") else 0,
        notes           = order.notes,
    )
    db.session.add(inv)
    db.session.flush()

    for ol in order.lines:
        db.session.add(AccSalesInvoiceLine(
            invoice_id   = inv.id,
            sequence     = ol.sequence,
            product_id   = ol.product_id,
            description  = ol.description,
            qty          = ol.qty,
            uom_id       = ol.uom_id,
            unit_price   = ol.unit_price,
            discount_pct = ol.discount_pct,
            subtotal     = ol.subtotal,
            account_id   = ol.account_id,
        ))

    for oc in order.charges:
        db.session.add(AccSalesInvoiceCharge(
            invoice_id = inv.id,
            charge_id  = oc.charge_id,
            sequence   = oc.sequence,
            base_amt   = oc.base_amt,
            amount     = oc.amount,
            account_id = oc.account_id,
        ))

    order.state = "partial" if order.state == "confirmed" else order.state
    db.session.commit()
    return inv
