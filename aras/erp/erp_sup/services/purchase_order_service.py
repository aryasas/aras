from arasCore.lib.core.extensions import db
from aras.erp.erp_sup.models.purchase_order import PurchaseOrder, PurchaseOrderLine, PurchaseOrderCharge
from aras.erp.erp_acc.models.invoice import AccPurchaseInvoice, AccPurchaseInvoiceLine, AccPurchaseInvoiceCharge
from aras.erp.erp_core.services import sequence as seq_svc


def confirm_order(order_id: int) -> PurchaseOrder:
    order = PurchaseOrder.get_or_404(order_id)
    if order.state != "draft":
        raise ValueError(f"Order {order.name} is already {order.state}.")
    order.state = "confirmed"
    db.session.commit()
    return order


def create_invoice_from_order(order_id: int) -> AccPurchaseInvoice:
    """Create a Purchase Invoice from a confirmed Purchase Order."""
    order = PurchaseOrder.get_or_404(order_id)
    if order.state not in ("confirmed", "partial"):
        raise ValueError(f"Order {order.name} must be confirmed before invoicing.")

    inv_name = seq_svc.next_code(order.company_id, "accounting.purchase_invoice")

    inv = AccPurchaseInvoice(
        company_id      = order.company_id,
        supplier_id     = order.supplier_id,
        location_id     = order.location_id,
        origin_order_id = order.id,
        name            = inv_name,
        invoice_date    = db.func.current_date(),
        currency_id     = order.currency_id,
        price_type_id   = order.price_type_id,
        subtotal        = order.subtotal,
        discount_amt    = order.discount_amt,
        charge_amt      = order.charge_amt,
        total           = order.total,
        notes           = order.notes,
    )
    db.session.add(inv)
    db.session.flush()

    for ol in order.lines:
        db.session.add(AccPurchaseInvoiceLine(
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
        db.session.add(AccPurchaseInvoiceCharge(
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
